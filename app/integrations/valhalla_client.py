from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamTimeoutError,
)


@dataclass
class RouteLeg:
    sequence: int          
    duration_seconds: float
    distance_km: float
    eta_offset_seconds: float  # seconds from route start


@dataclass
class RouteResult:
    total_distance_km: float
    total_duration_seconds: float
    legs: list[RouteLeg]
    raw_payload: dict | None = None


class ValhallaClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.base_url = (base_url or settings.valhalla_base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds or settings.valhalla_timeout_seconds
        self._http_client = http_client

    def optimized_route(self, locations: list[tuple[float, float]]) -> RouteResult:

        if len(locations) < 2:
            raise UpstreamNotFoundError("At least 2 locations are required for routing")

        body = {
            "locations": [
                {"lat": lat, "lon": lon, "type": "break"}
                for lat, lon in locations
            ],
            "costing": "auto",
            "directions_options": {"units": "kilometers"},
        }

        response = self._post(f"{self.base_url}/route", body)

        if response.status_code == 400:
            raise UpstreamNotFoundError("Valhalla could not find a route")
        if response.status_code >= 400:
            raise UpstreamBadResponseError(
                f"Valhalla returned HTTP {response.status_code}"
            )

        try:
            payload = response.json()
        except ValueError as exc:
            raise UpstreamBadResponseError("Valhalla returned invalid JSON") from exc

        return self._parse_route(payload)

    def _parse_route(self, payload: dict) -> RouteResult:
        try:
            trip = payload["trip"]
            summary = trip["summary"]
            raw_legs = trip["legs"]
        except KeyError as exc:
            raise UpstreamBadResponseError(f"Valhalla response missing field: {exc}") from exc

        total_distance_km = float(summary["length"])
        total_duration_seconds = float(summary["time"])

        legs: list[RouteLeg] = []
        cumulative_seconds = 0.0
        for i, leg in enumerate(raw_legs):
            leg_duration = float(leg["summary"]["time"])
            leg_distance = float(leg["summary"]["length"])
            legs.append(RouteLeg(
                sequence=i + 2,  # leg i connects stop i to stop i+1; ETA is for the arrival stop
                duration_seconds=leg_duration,
                distance_km=leg_distance,
                eta_offset_seconds=cumulative_seconds + leg_duration,
            ))
            cumulative_seconds += leg_duration

        return RouteResult(
            total_distance_km=total_distance_km,
            total_duration_seconds=total_duration_seconds,
            legs=legs,
            raw_payload=payload
        )

    def _post(self, url: str, body: dict) -> httpx.Response:
        if self._http_client is not None:
            return self._request_with_client(self._http_client, url, body)
        with httpx.Client(timeout=self.timeout_seconds) as client:
            return self._request_with_client(client, url, body)

    def _request_with_client(self, client: httpx.Client, url: str, body: dict) -> httpx.Response:
        try:
            return client.post(url, json=body)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError("Valhalla request timed out") from exc
        except httpx.HTTPError as exc:
            raise UpstreamBadResponseError("Valhalla request failed") from exc