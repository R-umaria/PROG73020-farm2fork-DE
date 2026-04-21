from __future__ import annotations

import re
from collections import defaultdict
from datetime import UTC, datetime, timedelta, timezone
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.delivery_status import DeliveryExecutionStatus, INITIAL_DELIVERY_EXECUTION_STATUS
from app.integrations.errors import UpstreamBadResponseError, UpstreamNotFoundError, UpstreamTimeoutError
from app.integrations.geocoding_client import GeocodingClient
from app.integrations.osrm_client import OsrmClient
from app.integrations.valhalla_client import ValhallaClient
from app.repositories.customer_repository import CustomerRepository
from app.repositories.execution_repository import ExecutionRepository
from app.repositories.planning_repository import PlanningRepository
from app.schemas.planning import (
    BacklogPlanningCandidate,
    BacklogPlanningGroup,
    BacklogPlanningSkip,
    GroupBacklogResponse,
    PlanningResponse,
    ScheduleRoutesResponse,
    ScheduledDriverAssignment,
    ScheduledRouteGroup,
    ScheduledRouteStop,
)
from app.schemas.routing import RouteCoordinate, RouteMapResponse, RouteMapWaypoint
from app.services.driver_assignment_policy import DriverAssignmentPolicy
from app.utils.polyline import decode_polyline

RegionSource = Literal["postal_prefix", "city_province"]
HandlingType = Literal["delivery", "pickup"]


class PlanningService:
    def __init__(
        self,
        db: Session | None = None,
        driver_assignment_policy: DriverAssignmentPolicy | None = None,
        geocoding_client: GeocodingClient | None = None,
        valhalla_client: ValhallaClient | None = None,
        osrm_client: OsrmClient | None = None,
    ):
        self.db: Session = db or SessionLocal()
        self.repo = PlanningRepository(self.db)
        self.execution_repo = ExecutionRepository(self.db)
        self.customer_repo = CustomerRepository(self.db)
        self.driver_assignment_policy = driver_assignment_policy or DriverAssignmentPolicy()
        self.geocoding_client = geocoding_client or GeocodingClient()
        self.valhalla_client = valhalla_client or ValhallaClient()
        self.osrm_client = osrm_client or OsrmClient()

    def geocode_pending_requests(self) -> PlanningResponse:
        pending = self.customer_repo.list_pending_geocodes()
        resolved_count = 0
        failed_count = 0

        for customer in pending:
            try:
                geocode = self.geocoding_client.geocode_address(
                    street=customer.street,
                    city=customer.city,
                    province=customer.province,
                    postal_code=customer.postal_code,
                    country=customer.country,
                )
                self.customer_repo.update_customer_geocode(
                    delivery_request_id=customer.delivery_request_id,
                    latitude=geocode.latitude,
                    longitude=geocode.longitude,
                    geocode_status="resolved",
                )
                resolved_count += 1

            except (UpstreamBadResponseError, UpstreamNotFoundError, UpstreamTimeoutError):
                self.customer_repo.update_geocode_status(
                    delivery_request_id=customer.delivery_request_id,
                    geocode_status="failed",
                )
                failed_count += 1

        return PlanningResponse(
            message="Pending geocoding completed",
            resolved_count=resolved_count,
            failed_count=failed_count,
        )

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
        next_route_index = self.repo.list_route_groups_count()

        for planning_group in grouped_backlog.groups:
            chunked_candidates = self._chunk_candidates(planning_group.candidates, settings.planning_max_orders_per_route)
            for chunk_number, candidate_chunk in enumerate(chunked_candidates, start=1):
                open_group = self.repo.find_open_group_for_planning(
                    group_key=planning_group.group_key,
                    capacity=settings.planning_max_orders_per_route,
                )
                if open_group is not None:
                    route_group = open_group
                    scheduled_date = route_group.scheduled_date
                    starting_sequence = len(route_group.stops) + 1
                else:
                    next_route_index += 1
                    first_candidate = candidate_chunk[0]
                    scheduled_date = self._scheduled_slot_for_route_index(first_candidate.request_timestamp, next_route_index - 1)
                    route_group = self.repo.create_route_group(
                        name=self._route_group_name(planning_group.group_key, scheduled_date, chunk_number),
                        scheduled_date=scheduled_date,
                        status="scheduled",
                        zone_code=planning_group.region_key,
                        total_stops=0,
                    )
                    starting_sequence = 1

                scheduled_stops: list[ScheduledRouteStop] = []
                for index, candidate in enumerate(candidate_chunk, start=starting_sequence):
                    offset_index = index - 1
                    estimated_arrival = scheduled_date + timedelta(minutes=15 * offset_index)
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

                route_group = self.repo.update_route_group_total_stops(
                    route_group_id=route_group.id,
                    total_stops=(route_group.total_stops or 0) + len(candidate_chunk),
                ) or route_group

                driver_assignment = None
                if settings.planning_auto_assign_drivers:
                    selected_driver = self.driver_assignment_policy.select_driver(self.repo.get_active_driver_loads())
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

                for candidate in candidate_chunk:
                    existing_execution = self.execution_repo.get_by_delivery_request_id(candidate.delivery_request_id)
                    if existing_execution is None:
                        self.execution_repo.create_execution(
                            delivery_request_id=candidate.delivery_request_id,
                            current_status=INITIAL_DELIVERY_EXECUTION_STATUS,
                        )

                self.optimize_route_group(route_group.id)

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

    def optimize_route_group(self, route_group_id: UUID) -> bool:
        group = self.repo.get_route_group_by_id(route_group_id)
        if group is None:
            return False

        valid_stops = self._routeable_stops(group)
        if not valid_stops:
            return False

        warehouse_location = (settings.warehouse_latitude, settings.warehouse_longitude)
        locations: list[tuple[float, float]] = [warehouse_location] + [
            (float(stop.delivery_request.customer_details.latitude), float(stop.delivery_request.customer_details.longitude))
            for stop in valid_stops
        ]

        result = self._route_locations(locations)
        if result is None:
            return False

        self.repo.update_route_group_routing(
            route_group_id=route_group_id,
            estimated_distance_km=result.total_distance_km,
            estimated_duration_min=max(1, int(round(result.total_duration_seconds / 60))) if result.total_duration_seconds > 0 else 0,
            route_payload=result.raw_payload,
        )

        departure_time = group.scheduled_date
        if departure_time is not None and departure_time.tzinfo is None:
            departure_time = departure_time.replace(tzinfo=timezone.utc)

        if departure_time is not None:
            for stop, leg in zip(valid_stops, result.legs):
                eta = departure_time + timedelta(seconds=leg.eta_offset_seconds)
                self.repo.update_route_stop_eta(
                    route_stop_id=stop.id,
                    estimated_arrival=eta,
                )

        return True

    def get_route_map(self, route_group_id: UUID) -> RouteMapResponse:
        group = self.repo.get_route_group_by_id(route_group_id)
        if group is None:
            raise ValueError(f"Route group {route_group_id} was not found")

        routeable_stops = self._routeable_stops(group)
        warehouse = RouteMapWaypoint(
            latitude=settings.warehouse_latitude,
            longitude=settings.warehouse_longitude,
            label=settings.warehouse_name,
            address=settings.warehouse_address,
            sequence=0,
        )

        stop_pairs = [
            (stop, self._build_route_waypoint(stop, geocoding_client=self.geocoding_client))
            for stop in routeable_stops
        ]

        active_origin, active_stop, active_sequence = self._determine_active_segment(warehouse, stop_pairs)
        path: list[RouteCoordinate] = []
        encoded_polyline: str | None = None
        routing_status = "completed" if active_stop is None else "fallback"
        provider = "No active route"
        segment_distance_km: float | None = None
        segment_duration_min: int | None = None
        segment_duration_seconds: float | None = None
        next_stop_eta: str | None = None

        if active_origin is not None and active_stop is not None and active_sequence is not None:
            segment_path, encoded_polyline, segment_distance_km, segment_duration_min, segment_duration_seconds = self._resolve_active_segment_route(
                group=group,
                origin=active_origin,
                destination=active_stop,
                sequence=active_sequence,
            )
            if encoded_polyline and segment_path:
                path = segment_path
                routing_status = "optimized"
                provider = "Live routing + OpenStreetMap"
            elif segment_path:
                path = segment_path
                routing_status = "optimized"
                provider = "Stored route geometry + OpenStreetMap"
            else:
                path = self._build_fallback_path(active_origin, [active_stop])
                routing_status = "fallback"
                provider = "Fallback path + OpenStreetMap"

            if segment_duration_seconds is not None:
                next_stop_eta = (datetime.now(timezone.utc) + timedelta(seconds=segment_duration_seconds)).isoformat()
            elif segment_duration_min is not None:
                next_stop_eta = (datetime.now(timezone.utc) + timedelta(minutes=segment_duration_min)).isoformat()

        return RouteMapResponse(
            route_group_id=group.id,
            route_group_name=group.name,
            route_group_status=group.status,
            routing_status=routing_status,
            provider=provider,
            warehouse=warehouse,
            stops=[active_stop] if active_stop is not None else [],
            path=path,
            encoded_polyline=encoded_polyline,
            estimated_distance_km=float(group.estimated_distance_km) if group.estimated_distance_km is not None else None,
            estimated_duration_min=group.estimated_duration_min,
            active_origin=active_origin,
            active_stop=active_stop,
            segment_distance_km=segment_distance_km,
            segment_duration_min=segment_duration_min,
            next_stop_eta=next_stop_eta,
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

        handling_type = self._derive_handling_type(delivery_request)
        if handling_type == "pickup":
            return "pickup_not_route_grouped"

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
            if order_type is None and isinstance(raw_payload.get("pickup"), bool):
                order_type = "pickup" if raw_payload.get("pickup") else "delivery"

        if isinstance(order_type, str) and order_type.strip().lower() == "pickup":
            return "pickup"

        return "delivery"

    @staticmethod
    def _route_group_name(group_key: str, scheduled_date, chunk_number: int) -> str:
        normalized_group_key = group_key.replace(" ", "_")
        return f"route-group:{normalized_group_key}:part{chunk_number}:{scheduled_date.strftime('%Y%m%dT%H%M%SZ')}"

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

    @staticmethod
    def _routeable_stops(group) -> list:
        stops = sorted(group.stops, key=lambda stop: (stop.sequence, str(stop.id)))
        routeable = []
        for stop in stops:
            customer_details = stop.delivery_request.customer_details if stop.delivery_request else None
            if customer_details is None:
                continue
            if customer_details.latitude is None or customer_details.longitude is None:
                continue
            routeable.append(stop)
        return routeable

    @staticmethod
    def _build_route_waypoint(stop, geocoding_client: GeocodingClient | None = None) -> RouteMapWaypoint:
        customer_details = stop.delivery_request.customer_details
        assert customer_details is not None

        latitude = float(customer_details.latitude) if customer_details.latitude is not None else None
        longitude = float(customer_details.longitude) if customer_details.longitude is not None else None

        if latitude is None or longitude is None:
            if geocoding_client is not None:
                try:
                    precise = geocoding_client.geocode_address(
                        street=customer_details.street,
                        city=customer_details.city,
                        province=customer_details.province,
                        postal_code=customer_details.postal_code,
                        country=customer_details.country,
                    )
                    latitude = precise.latitude
                    longitude = precise.longitude
                except (UpstreamBadResponseError, UpstreamNotFoundError, UpstreamTimeoutError):
                    pass

        if latitude is None or longitude is None:
            raise ValueError(f"Route stop {stop.id} is missing usable coordinates")

        return RouteMapWaypoint(
            latitude=latitude,
            longitude=longitude,
            label=customer_details.customer_name,
            address=", ".join(
                part.strip()
                for part in [
                    customer_details.street,
                    customer_details.city,
                    customer_details.province,
                    customer_details.postal_code,
                    customer_details.country,
                ]
                if isinstance(part, str) and part.strip()
            ) or None,
            sequence=stop.sequence,
            route_stop_id=stop.id,
            delivery_request_id=stop.delivery_request_id,
            order_id=stop.delivery_request.order_id if stop.delivery_request is not None else None,
            stop_status=stop.stop_status,
        )

    @staticmethod
    def _determine_active_segment(
        warehouse: RouteMapWaypoint,
        stop_pairs: list[tuple[object, RouteMapWaypoint]],
    ) -> tuple[RouteMapWaypoint | None, RouteMapWaypoint | None, int | None]:
        if not stop_pairs:
            return warehouse, None, None

        last_completed_waypoint: RouteMapWaypoint | None = None
        for stop, waypoint in stop_pairs:
            if str(getattr(stop, "stop_status", "")).lower() == "completed":
                last_completed_waypoint = waypoint
                continue
            return (last_completed_waypoint or warehouse), waypoint, waypoint.sequence

        return (last_completed_waypoint or warehouse), None, None

    def _resolve_active_segment_route(
        self,
        *,
        group,
        origin: RouteMapWaypoint,
        destination: RouteMapWaypoint,
        sequence: int,
    ) -> tuple[list[RouteCoordinate], str | None, float | None, int | None, float | None]:
        result = self._route_locations([
            (origin.latitude, origin.longitude),
            (destination.latitude, destination.longitude),
        ])
        if result is not None:
            raw_polyline = (result.encoded_polylines or [None])[0] or None
            path = self._decode_polyline_coordinates(raw_polyline)
            duration_seconds = result.total_duration_seconds
            duration_min = max(1, int(round(duration_seconds / 60))) if duration_seconds > 0 else 0
            if path:
                return path, raw_polyline, result.total_distance_km, duration_min, duration_seconds

        _payload_polyline, payload_path, payload_distance_km, payload_duration_min, payload_duration_seconds = self._decode_route_payload_leg(group.route_payload, sequence)
        if payload_path:
            return payload_path, None, payload_distance_km, payload_duration_min, payload_duration_seconds

        return [], None, None, None, None

    @classmethod
    def _decode_route_payload_leg(cls, route_payload: dict | None, sequence: int) -> tuple[str | None, list[RouteCoordinate], float | None, int | None, float | None]:
        if not isinstance(route_payload, dict) or sequence < 1:
            return None, [], None, None, None

        trip = route_payload.get("trip")
        if not isinstance(trip, dict):
            return None, [], None, None, None

        legs = trip.get("legs")
        if not isinstance(legs, list) or sequence > len(legs):
            return None, [], None, None, None

        leg = legs[sequence - 1]
        if not isinstance(leg, dict):
            return None, [], None, None, None

        encoded_shape = leg.get("shape")
        encoded_polyline = encoded_shape if isinstance(encoded_shape, str) and encoded_shape else None
        points = cls._decode_polyline_coordinates(encoded_polyline)
        summary = leg.get("summary") if isinstance(leg.get("summary"), dict) else {}
        distance_km = float(summary["length"]) if "length" in summary else None
        duration_seconds = float(summary["time"]) if "time" in summary else None
        duration_min = max(1, int(round(duration_seconds / 60))) if duration_seconds is not None and duration_seconds > 0 else (0 if duration_seconds == 0 else None)
        return encoded_polyline, points, distance_km, duration_min, duration_seconds

    def _route_locations(self, locations: list[tuple[float, float]]):
        if len(locations) < 2:
            return None

        if settings.valhalla_enable_routing:
            try:
                return self.valhalla_client.optimized_route(locations)
            except Exception:
                pass

        if settings.osrm_enable_routing:
            try:
                return self.osrm_client.route(locations)
            except Exception:
                pass

        return None

    @staticmethod
    def _decode_polyline_coordinates(encoded_polyline: str | None) -> list[RouteCoordinate]:
        if not encoded_polyline:
            return []

        try:
            return [
                RouteCoordinate(latitude=lat, longitude=lon)
                for lat, lon in decode_polyline(encoded_polyline, precision=6)
            ]
        except Exception:
            return []

    @staticmethod
    def _build_fallback_path(warehouse: RouteMapWaypoint, stops: list[RouteMapWaypoint]) -> list[RouteCoordinate]:
        coordinates = [
            RouteCoordinate(latitude=warehouse.latitude, longitude=warehouse.longitude),
            *[RouteCoordinate(latitude=stop.latitude, longitude=stop.longitude) for stop in stops],
        ]
        deduped: list[RouteCoordinate] = []
        for coordinate in coordinates:
            if not deduped or deduped[-1] != coordinate:
                deduped.append(coordinate)
        return deduped

    @staticmethod
    def _chunk_candidates(candidates: list[BacklogPlanningCandidate], max_size: int) -> list[list[BacklogPlanningCandidate]]:
        if max_size <= 0:
            max_size = 50
        return [candidates[index:index + max_size] for index in range(0, len(candidates), max_size)]

    @staticmethod
    def _next_business_day_start(reference: datetime) -> datetime:
        tz = ZoneInfo(settings.planning_timezone)
        local_reference = reference.astimezone(tz) if reference.tzinfo else reference.replace(tzinfo=UTC).astimezone(tz)
        local_reference = local_reference.replace(
            hour=settings.planning_workday_start_hour, minute=0, second=0, microsecond=0
        )
        while local_reference.weekday() >= 5:
            local_reference += timedelta(days=1)
            local_reference = local_reference.replace(hour=settings.planning_workday_start_hour, minute=0, second=0, microsecond=0)
        return local_reference.astimezone(UTC)

    def _scheduled_slot_for_route_index(self, reference: datetime, route_index: int) -> datetime:
        daily_capacity = max(1, settings.planning_daily_route_capacity)
        business_day_offset = route_index // daily_capacity
        same_day_slot = route_index % daily_capacity

        start = self._next_business_day_start(reference)
        tz = ZoneInfo(settings.planning_timezone)
        local_start = start.astimezone(tz)

        while business_day_offset > 0:
            local_start += timedelta(days=1)
            local_start = local_start.replace(hour=settings.planning_workday_start_hour, minute=0, second=0, microsecond=0)
            if local_start.weekday() < 5:
                business_day_offset -= 1

        local_start = local_start + timedelta(minutes=same_day_slot * 2)
        return local_start.astimezone(UTC)
