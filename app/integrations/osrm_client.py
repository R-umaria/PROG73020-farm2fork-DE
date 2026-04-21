from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamTimeoutError,
)
from app.integrations.valhalla_client import RouteLeg, RouteResult


@dataclass
class OsrmSegment:
    geometry: str
    distance_meters: float
    duration_seconds: float


class OsrmClient:
    """Road routing client backed by the public OSRM API.

    OSRM is used as a resilient fallback when a local Valhalla instance is not
    available. It is also safe for routing a single active leg on demand.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.base_url = (base_url or settings.osrm_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.osrm_timeout_seconds
        self._http_client = http_client

    def route(self, locations: list[tuple[float, float]]) -> RouteResult:
        if len(locations) < 2:
            raise UpstreamNotFoundError("At least 2 locations are required for routing")

        total_distance_km = 0.0
        total_duration_seconds = 0.0
        eta_offset_seconds = 0.0
        legs: list[RouteLeg] = []
        raw_legs: list[dict] = []
        encoded_polylines: list[str] = []

        for sequence, (origin, destination) in enumerate(zip(locations, locations[1:]), start=1):
            segment = self.route_segment(origin=origin, destination=destination)
            distance_km = segment.distance_meters / 1000.0
            total_distance_km += distance_km
            total_duration_seconds += segment.duration_seconds
            eta_offset_seconds += segment.duration_seconds
            encoded_polylines.append(segment.geometry)
            legs.append(
                RouteLeg(
                    sequence=sequence,
                    duration_seconds=segment.duration_seconds,
                    distance_km=distance_km,
                    eta_offset_seconds=eta_offset_seconds,
                )
            )
            raw_legs.append(
                {
                    "shape": segment.geometry,
                    "summary": {
                        "length": distance_km,
                        "time": segment.duration_seconds,
                    },
                }
            )

        raw_payload = {
            "provider": "osrm",
            "trip": {
                "summary": {
                    "length": total_distance_km,
                    "time": total_duration_seconds,
                },
                "legs": raw_legs,
            },
        }

        return RouteResult(
            total_distance_km=total_distance_km,
            total_duration_seconds=total_duration_seconds,
            legs=legs,
            raw_payload=raw_payload,
            encoded_polylines=encoded_polylines,
        )

    def route_segment(
        self,
        *,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ) -> OsrmSegment:
        origin_lat, origin_lon = origin
        destination_lat, destination_lon = destination
        path = (
            f"/route/v1/driving/{origin_lon},{origin_lat};{destination_lon},{destination_lat}"
            "?overview=full&geometries=polyline6"
        )
        response = self._get(f"{self.base_url}{path}")

        if response.status_code == 400:
            raise UpstreamNotFoundError("OSRM could not find a route")
        if response.status_code >= 400:
            raise UpstreamBadResponseError(f"OSRM returned HTTP {response.status_code}")

        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamBadResponseError("OSRM returned invalid JSON") from exc

        if payload.get("code") != "Ok":
            raise UpstreamBadResponseError("OSRM returned a non-Ok routing response")

        routes = payload.get("routes")
        if not isinstance(routes, list) or not routes:
            raise UpstreamNotFoundError("OSRM returned no routes")

        first_route = routes[0]
        geometry = first_route.get("geometry")
        distance_meters = first_route.get("distance")
        duration_seconds = first_route.get("duration")
        if not isinstance(geometry, str) or not geometry:
            raise UpstreamBadResponseError("OSRM route is missing geometry")
        if not isinstance(distance_meters, (int, float)):
            raise UpstreamBadResponseError("OSRM route is missing distance")
        if not isinstance(duration_seconds, (int, float)):
            raise UpstreamBadResponseError("OSRM route is missing duration")

        return OsrmSegment(
            geometry=geometry,
            distance_meters=float(distance_meters),
            duration_seconds=float(duration_seconds),
        )

    def _get(self, url: str) -> httpx.Response:
        if self._http_client is not None:
            return self._request_with_client(self._http_client, url)
        with httpx.Client(timeout=self.timeout_seconds, headers={"User-Agent": settings.geocoding_user_agent}) as client:
            return self._request_with_client(client, url)

    @staticmethod
    def _request_with_client(client: httpx.Client, url: str) -> httpx.Response:
        try:
            return client.get(url)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError("OSRM request timed out") from exc
        except httpx.HTTPError as exc:
            raise UpstreamBadResponseError("OSRM request failed") from exc
