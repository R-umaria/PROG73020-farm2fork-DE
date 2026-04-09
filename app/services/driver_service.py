from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.integrations.driver_service_client import DriverServiceClient
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
        self.client = driver_client or DriverServiceClient()

    def list_drivers(self) -> list[DriverSummaryResponse]:
        return self.client.list_drivers()

    def get_todays_schedule(self, driver_id: int) -> DriverScheduleResponse:
        driver = self.client.get_driver(driver_id)
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
            for stop in self.repo.list_driver_route_stops(driver_id)
        ]
        return DriverScheduleResponse(
            driver_id=driver.driver_id,
            driver_name=driver.driver_name,
            vehicle_type=driver.vehicle_type,
            driver_status=driver.driver_status,
            stops=stops,
        )

    def start_day(self, driver_id: int) -> DriverDayActionResponse:
        driver = self.client.get_driver(driver_id)
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
