from __future__ import annotations

import re
from collections import defaultdict
from datetime import timedelta
from typing import Literal

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.delivery_status import INITIAL_DELIVERY_EXECUTION_STATUS
from app.repositories.execution_repository import ExecutionRepository
from app.repositories.planning_repository import PlanningRepository
from app.schemas.planning import (
    BacklogPlanningCandidate,
    BacklogPlanningGroup,
    BacklogPlanningSkip,
    GroupBacklogResponse,
    ScheduleRoutesResponse,
    ScheduledDriverAssignment,
    ScheduledRouteGroup,
    ScheduledRouteStop,
)
from app.services.driver_assignment_policy import DriverAssignmentPolicy

RegionSource = Literal["postal_prefix", "city_province"]
HandlingType = Literal["delivery", "pickup"]


class PlanningService:
    def __init__(
        self,
        db: Session | None = None,
        driver_assignment_policy: DriverAssignmentPolicy | None = None,
    ):
        self.db: Session = db or SessionLocal()
        self.repo = PlanningRepository(self.db)
        self.execution_repo = ExecutionRepository(self.db)
        self.driver_assignment_policy = driver_assignment_policy or DriverAssignmentPolicy()

    def geocode_pending_requests(self):
        return {"message": "Pending addresses geocoded placeholder"}

    def group_backlog(self) -> GroupBacklogResponse:
        grouped: dict[tuple[str, str], list[BacklogPlanningCandidate]] = defaultdict(list)
        skips: list[BacklogPlanningSkip] = []

        for delivery_request in self.repo.list_backlog_requests():
            reason = self._ineligibility_reason(delivery_request)
            if reason is not None:
                skips.append(
                    BacklogPlanningSkip(
                        delivery_request_id=delivery_request.id,
                        order_id=delivery_request.order_id,
                        reason=reason,
                    )
                )
                continue

            customer_details = delivery_request.customer_details
            assert customer_details is not None

            region_key, region_source, postal_prefix = self.derive_region_key(
                postal_code=customer_details.postal_code,
                city=customer_details.city,
                province=customer_details.province,
            )
            handling_type = self._derive_handling_type(delivery_request)

            candidate = BacklogPlanningCandidate(
                delivery_request_id=delivery_request.id,
                order_id=delivery_request.order_id,
                customer_id=delivery_request.customer_id,
                handling_type=handling_type,
                region_key=region_key,
                region_source=region_source,
                postal_prefix=postal_prefix,
                city=customer_details.city,
                province=customer_details.province,
                request_timestamp=delivery_request.request_timestamp,
            )
            grouped[(handling_type, region_key)].append(candidate)

        groups: list[BacklogPlanningGroup] = []
        for (handling_type, region_key), candidates in sorted(grouped.items(), key=lambda item: item[0]):
            sorted_candidates = sorted(
                candidates,
                key=lambda candidate: (
                    candidate.request_timestamp,
                    candidate.order_id,
                    str(candidate.delivery_request_id),
                ),
            )
            first_candidate = sorted_candidates[0]
            groups.append(
                BacklogPlanningGroup(
                    group_key=f"{handling_type}:{region_key}",
                    handling_type=handling_type,
                    region_key=region_key,
                    region_source=first_candidate.region_source,
                    request_count=len(sorted_candidates),
                    candidates=sorted_candidates,
                )
            )

        sorted_skips = sorted(skips, key=lambda skip: (skip.order_id, str(skip.delivery_request_id)))
        total_candidates = sum(group.request_count for group in groups)
        return GroupBacklogResponse(
            message="Backlog grouped deterministically (v1)",
            total_groups=len(groups),
            total_candidates=total_candidates,
            skipped_count=len(sorted_skips),
            groups=groups,
            skipped_requests=sorted_skips,
        )

    def schedule_routes(self) -> ScheduleRoutesResponse:
        grouped_backlog = self.group_backlog()
        scheduled_groups: list[ScheduledRouteGroup] = []

        for planning_group in grouped_backlog.groups:
            first_candidate = planning_group.candidates[0]
            scheduled_date = first_candidate.request_timestamp
            route_group = self.repo.create_route_group(
                name=self._route_group_name(planning_group.group_key, scheduled_date),
                scheduled_date=scheduled_date,
                status="scheduled",
                zone_code=planning_group.region_key,
                total_stops=planning_group.request_count,
            )

            scheduled_stops: list[ScheduledRouteStop] = []
            for index, candidate in enumerate(planning_group.candidates, start=1):
                estimated_arrival = scheduled_date + timedelta(minutes=15 * (index - 1))
                route_stop = self.repo.add_route_stop(
                    route_group_id=route_group.id,
                    delivery_request_id=candidate.delivery_request_id,
                    sequence=index,
                    estimated_arrival=estimated_arrival,
                    stop_status="planned",
                )
                scheduled_stops.append(
                    ScheduledRouteStop(
                        route_stop_id=route_stop.id,
                        delivery_request_id=candidate.delivery_request_id,
                        order_id=candidate.order_id,
                        sequence=index,
                        stop_status=route_stop.stop_status,
                        estimated_arrival=estimated_arrival,
                    )
                )

            selected_driver = self.driver_assignment_policy.select_driver(self.repo.get_active_driver_loads())
            driver_assignment = None
            if selected_driver is not None:
                assignment = self.repo.assign_driver(
                    route_group_id=route_group.id,
                    driver_id=selected_driver.driver.id,
                    assignment_status="assigned",
                )
                driver_assignment = ScheduledDriverAssignment(
                    driver_id=assignment.driver_id,
                    driver_name=selected_driver.driver.name,
                    vehicle_type=selected_driver.driver.vehicle_type,
                    driver_status=selected_driver.driver.status,
                    assignment_status=assignment.assignment_status,
                    current_load_before_assignment=selected_driver.current_load,
                )

            # Scheduling is the explicit point where an execution enters the canonical
            # `scheduled` state, so we create that execution record once the route,
            # stops, and any initial assignment already exist.
            for candidate in planning_group.candidates:
                existing_execution = self.execution_repo.get_by_delivery_request_id(candidate.delivery_request_id)
                if existing_execution is None:
                    self.execution_repo.create_execution(
                        delivery_request_id=candidate.delivery_request_id,
                        current_status=INITIAL_DELIVERY_EXECUTION_STATUS,
                    )

            scheduled_groups.append(
                ScheduledRouteGroup(
                    route_group_id=route_group.id,
                    group_key=planning_group.group_key,
                    route_group_name=route_group.name,
                    handling_type=planning_group.handling_type,
                    zone_code=route_group.zone_code,
                    scheduled_date=route_group.scheduled_date,
                    route_group_status=route_group.status,
                    total_stops=route_group.total_stops,
                    driver_assignment=driver_assignment,
                    stops=scheduled_stops,
                )
            )

        assigned_group_count = sum(1 for group in scheduled_groups if group.driver_assignment is not None)
        unassigned_group_count = len(scheduled_groups) - assigned_group_count
        return ScheduleRoutesResponse(
            message="Route groups scheduled deterministically (v1)",
            scheduled_group_count=len(scheduled_groups),
            assigned_group_count=assigned_group_count,
            unassigned_group_count=unassigned_group_count,
            route_groups=scheduled_groups,
        )

    def close(self) -> None:
        self.db.close()

    @classmethod
    def derive_region_key(
        cls,
        *,
        postal_code: str | None,
        city: str,
        province: str,
    ) -> tuple[str, RegionSource, str | None]:
        postal_prefix = cls._postal_prefix(postal_code)
        if postal_prefix is not None:
            return f"postal_prefix:{postal_prefix}", "postal_prefix", postal_prefix

        normalized_city = cls._normalize_text_token(city)
        normalized_province = cls._normalize_text_token(province)
        return f"city_province:{normalized_city}:{normalized_province}", "city_province", None

    def _ineligibility_reason(self, delivery_request) -> str | None:
        if delivery_request.route_stops:
            return "already_grouped"

        customer_details = delivery_request.customer_details
        if customer_details is None:
            return "missing_customer_enrichment"

        required_fields = {
            "street": customer_details.street,
            "city": customer_details.city,
            "province": customer_details.province,
            "country": customer_details.country,
        }
        missing_required = [name for name, value in required_fields.items() if not self._has_text(value)]
        if missing_required:
            return f"missing_customer_fields:{','.join(sorted(missing_required))}"

        has_postal_prefix = self._postal_prefix(customer_details.postal_code) is not None
        has_city_province = self._has_text(customer_details.city) and self._has_text(customer_details.province)
        if not has_postal_prefix and not has_city_province:
            return "missing_region_inputs"

        return None

    def _derive_handling_type(self, delivery_request) -> HandlingType:
        order_type = None
        if delivery_request.request_snapshot is not None:
            raw_payload = delivery_request.request_snapshot.request_payload or {}
            order_type = raw_payload.get("order_type")

        if isinstance(order_type, str) and order_type.strip().lower() == "pickup":
            return "pickup"

        return "delivery"

    @staticmethod
    def _route_group_name(group_key: str, scheduled_date) -> str:
        normalized_group_key = group_key.replace(" ", "_")
        return f"route-group:{normalized_group_key}:{scheduled_date.strftime('%Y%m%dT%H%M%SZ')}"

    @staticmethod
    def _postal_prefix(postal_code: str | None) -> str | None:
        if not isinstance(postal_code, str):
            return None
        normalized = re.sub(r"[^A-Za-z0-9]", "", postal_code).upper()
        if len(normalized) >= 3:
            return normalized[:3]
        return None

    @staticmethod
    def _normalize_text_token(value: str) -> str:
        cleaned = re.sub(r"\s+", "_", value.strip().upper())
        cleaned = re.sub(r"[^A-Z0-9_]", "", cleaned)
        return cleaned

    @staticmethod
    def _has_text(value: str | None) -> bool:
        return isinstance(value, str) and bool(value.strip())
