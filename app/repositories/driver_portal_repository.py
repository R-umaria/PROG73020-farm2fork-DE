from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.models.db_models import DeliveryRequest, DriverAccount, DriverAssignment, RouteGroup, RouteStop

ACTIVE_ASSIGNMENT_STATUSES = {"assigned", "accepted"}
AVAILABLE_SHIFT_STATUSES = {"draft", "scheduled"}


class ShiftUnavailableError(ValueError):
    pass


class DriverPortalRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_driver_account_by_email(self, email: str) -> DriverAccount | None:
        return self.db.query(DriverAccount).filter(DriverAccount.email == email.strip().lower()).filter(DriverAccount.is_active.is_(True)).first()

    def get_driver_account_by_driver_id(self, driver_id: int) -> DriverAccount | None:
        return self.db.query(DriverAccount).filter(DriverAccount.driver_id == driver_id).filter(DriverAccount.is_active.is_(True)).first()

    def list_driver_accounts(self) -> list[DriverAccount]:
        return self.db.query(DriverAccount).filter(DriverAccount.is_active.is_(True)).order_by(DriverAccount.driver_name.asc(), DriverAccount.driver_id.asc()).all()

    def create_or_update_driver_account(self, *, driver_id: int, email: str, driver_name: str, vehicle_type: str, driver_status: str = "available", password_hash: str | None = None) -> DriverAccount:
        account = self.get_driver_account_by_driver_id(driver_id) or self.get_driver_account_by_email(email)
        if account is None:
            account = DriverAccount(driver_id=driver_id, email=email.strip().lower(), driver_name=driver_name, vehicle_type=vehicle_type, driver_status=driver_status, password_hash=password_hash, is_active=True)
            self.db.add(account)
        else:
            account.driver_id = driver_id
            account.email = email.strip().lower()
            account.driver_name = driver_name
            account.vehicle_type = vehicle_type
            account.driver_status = driver_status
            account.password_hash = password_hash
            account.is_active = True
        self.db.commit(); self.db.refresh(account); return account

    def get_active_route_group_for_driver(self, driver_id: int) -> RouteGroup | None:
        groups = self.db.query(RouteGroup).join(DriverAssignment, DriverAssignment.route_group_id == RouteGroup.id).options(selectinload(RouteGroup.driver_assignments)).filter(DriverAssignment.driver_id == driver_id).filter(DriverAssignment.assignment_status.in_(ACTIVE_ASSIGNMENT_STATUSES)).filter(RouteGroup.status.in_(["draft", "scheduled", "in_progress"])).order_by(RouteGroup.updated_at.desc(), RouteGroup.scheduled_date.asc()).all()
        return groups[0] if groups else None

    def list_available_route_groups(self) -> list[RouteGroup]:
        groups = self.db.query(RouteGroup).options(selectinload(RouteGroup.stops).selectinload(RouteStop.delivery_request).selectinload(DeliveryRequest.customer_details), selectinload(RouteGroup.driver_assignments)).order_by(RouteGroup.scheduled_date.asc(), RouteGroup.name.asc()).all()
        return [group for group in groups if self._is_group_available(group)]

    def claim_route_group(self, *, route_group_id: UUID, driver_id: int) -> RouteGroup:
        group = self.db.query(RouteGroup).options(selectinload(RouteGroup.stops).selectinload(RouteStop.delivery_request).selectinload(DeliveryRequest.execution), selectinload(RouteGroup.driver_assignments)).filter(RouteGroup.id == route_group_id).with_for_update().first()
        if group is None:
            raise ShiftUnavailableError(f"Shift {route_group_id} was not found")
        if not self._is_group_available(group):
            raise ShiftUnavailableError("This shift has already been claimed by another driver")
        now = datetime.now(tz=UTC)
        self.db.add(DriverAssignment(route_group_id=group.id, driver_id=driver_id, assignment_status="accepted", assigned_at=now, acknowledged_at=now))
        group.status = "in_progress"
        self.db.commit(); self.db.refresh(group)
        return self.get_route_group(group.id)  # type: ignore[return-value]

    def get_route_group(self, route_group_id: UUID) -> RouteGroup | None:
        return self.db.query(RouteGroup).options(selectinload(RouteGroup.stops).selectinload(RouteStop.delivery_request).selectinload(DeliveryRequest.customer_details), selectinload(RouteGroup.stops).selectinload(RouteStop.delivery_request).selectinload(DeliveryRequest.execution), selectinload(RouteGroup.driver_assignments)).filter(RouteGroup.id == route_group_id).first()

    @staticmethod
    def _is_group_available(group: RouteGroup) -> bool:
        if group.status not in AVAILABLE_SHIFT_STATUSES:
            return False
        active_assignments = [a for a in group.driver_assignments if a.assignment_status in ACTIVE_ASSIGNMENT_STATUSES and a.unassigned_at is None]
        return len(active_assignments) == 0
