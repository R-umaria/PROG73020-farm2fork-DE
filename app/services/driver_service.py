from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.integrations.driver_service_client import DriverServiceClient
from app.repositories.driver_portal_repository import DriverPortalRepository
from app.repositories.planning_repository import PlanningRepository
from app.schemas.driver import (
    DriverDayActionResponse,
    DriverScheduleResponse,
    DriverScheduleStopResponse,
    DriverSummaryResponse,
    RouteStopActionResponse,
)


class RouteStopNotFoundError(ValueError):
    """Raised when a route stop cannot be found."""


class DriverService:
    def __init__(
        self,
        db: Session | None = None,
        *,
        driver_client: DriverServiceClient | None = None,
    ):
        self.db: Session = db or SessionLocal()
        self.repo = PlanningRepository(self.db)
        self.portal_repo = DriverPortalRepository(self.db)
        self.client = driver_client or DriverServiceClient()

    def list_drivers(self) -> list[DriverSummaryResponse]:
        local_accounts = self.portal_repo.list_driver_accounts()
        if local_accounts:
            return [DriverSummaryResponse(driver_id=a.driver_id, driver_name=a.driver_name, vehicle_type=a.vehicle_type, driver_status=a.driver_status) for a in local_accounts]
        return self.client.list_drivers()

    def get_todays_schedule(self, driver_id: int, route_group_id: UUID | None = None) -> DriverScheduleResponse:
        driver = self._get_driver_summary(driver_id)
        stops = [
            DriverScheduleStopResponse(
                route_stop_id=stop.id,
                route_group_id=stop.route_group_id,
                delivery_request_id=stop.delivery_request_id,
                order_id=stop.delivery_request.order_id,
                sequence=stop.sequence,
                stop_status=stop.stop_status,
                estimated_arrival=stop.estimated_arrival,
                address=self._format_stop_address(stop.delivery_request.customer_details),
            )
            for stop in self.repo.list_driver_route_stops(driver_id, route_group_id=route_group_id)
        ]
        return DriverScheduleResponse(
            driver_id=driver.driver_id,
            driver_name=driver.driver_name,
            vehicle_type=driver.vehicle_type,
            driver_status=driver.driver_status,
            stops=stops,
        )

    def start_day(self, driver_id: int) -> DriverDayActionResponse:
        driver = self._get_driver_summary(driver_id)
        return DriverDayActionResponse(
            driver_id=driver.driver_id,
            driver_name=driver.driver_name,
            driver_status=driver.driver_status,
            message="Driver day started (v1)",
        )

    def complete_stop(self, route_stop_id: UUID) -> RouteStopActionResponse:
        stop = self.repo.update_route_stop_status(route_stop_id=route_stop_id, stop_status="completed")
        if stop is None:
            raise RouteStopNotFoundError(f"Route stop {route_stop_id} was not found")

        return RouteStopActionResponse(
            route_stop_id=stop.id,
            stop_status=stop.stop_status,
            message="Route stop marked completed (v1)",
        )

    def close(self) -> None:
        self.db.close()

    def _get_driver_summary(self, driver_id: int) -> DriverSummaryResponse:
        account = self.portal_repo.get_driver_account_by_driver_id(driver_id)
        if account is not None:
            return DriverSummaryResponse(driver_id=account.driver_id, driver_name=account.driver_name, vehicle_type=account.vehicle_type, driver_status=account.driver_status)
        return self.client.get_driver(driver_id)

    @staticmethod
    def _format_stop_address(customer_details) -> str | None:
        if customer_details is None:
            return None

        parts = [
            customer_details.street,
            customer_details.city,
            customer_details.province,
            customer_details.postal_code,
            customer_details.country,
        ]
        cleaned_parts = [str(part).strip() for part in parts if isinstance(part, str) and part.strip()]
        return ", ".join(cleaned_parts) if cleaned_parts else None
