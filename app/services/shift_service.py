from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.delivery_status import DeliveryExecutionStatus, InvalidStatusTransitionError
from app.integrations.customer_status_client import CustomerStatusClient
from app.repositories.driver_portal_repository import DriverPortalRepository
from app.repositories.execution_repository import ExecutionRepository
from app.schemas.shift import AvailableShiftResponse, StartShiftResponse


class ShiftService:
    def __init__(self, db: Session | None = None):
        self.db: Session = db or SessionLocal()
        self.repo = DriverPortalRepository(self.db)
        self.execution_repo = ExecutionRepository(self.db)
        self.customer_status_client = CustomerStatusClient()

    def list_available_shifts(self) -> list[AvailableShiftResponse]:
        results = []
        for group in self.repo.list_available_route_groups():
            ordered = sorted(group.stops, key=lambda stop: (stop.sequence, str(stop.id)))
            eta_values = [stop.estimated_arrival for stop in ordered if stop.estimated_arrival is not None]
            preview = []
            for stop in ordered[:3]:
                details = stop.delivery_request.customer_details
                preview.append(f"{details.city}, {details.postal_code[:3].upper()}" if details is not None else f"Order #{stop.delivery_request.order_id}")
            results.append(AvailableShiftResponse(
                route_group_id=group.id,
                shift_name=group.name,
                zone_code=group.zone_code,
                route_group_status=group.status,
                total_stops=group.total_stops,
                estimated_distance_km=float(group.estimated_distance_km) if group.estimated_distance_km is not None else None,
                estimated_duration_min=group.estimated_duration_min,
                scheduled_date=self._ensure_utc(group.scheduled_date),
                first_eta=self._ensure_utc(min(eta_values)) if eta_values else None,
                last_eta=self._ensure_utc(max(eta_values)) if eta_values else None,
                warehouse_name=settings.warehouse_name,
                warehouse_address=settings.warehouse_address,
                stop_preview=preview,
            ))
        return results

    def start_shift(self, *, route_group_id: UUID, driver_id: int) -> StartShiftResponse:
        driver = self.repo.get_driver_account_by_driver_id(driver_id)
        if driver is None:
            raise ValueError(f"Driver {driver_id} does not have an active local account")
        group = self.repo.claim_route_group(route_group_id=route_group_id, driver_id=driver_id)
        updated = 0; order_ids = []
        for stop in sorted(group.stops, key=lambda stop: (stop.sequence, str(stop.id))):
            execution = stop.delivery_request.execution
            if execution is None:
                continue
            try:
                self.execution_repo.update_status(delivery_execution_id=execution.id, new_status=DeliveryExecutionStatus.OUT_FOR_DELIVERY, changed_by=driver.email, reason=f"Shift {group.name} started by {driver.driver_name}")
                updated += 1; order_ids.append(stop.delivery_request.order_id)
            except InvalidStatusTransitionError:
                continue
        sync = self.customer_status_client.notify_orders_dispatched(order_ids)
        self.db.refresh(group); self.db.refresh(driver)
        return StartShiftResponse(route_group_id=group.id, shift_name=group.name, route_group_status=group.status, driver_id=driver.driver_id, driver_name=driver.driver_name, vehicle_type=driver.vehicle_type, driver_status=driver.driver_status, updated_delivery_count=updated, external_sync_status=sync.status)

    def close(self) -> None:
        self.db.close()

    @staticmethod
    def _ensure_utc(value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
