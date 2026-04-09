"""Driver service adapter with explicit development fallback and response validation."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import TypeAdapter, ValidationError

from app.core.config import settings
from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamTimeoutError,
)
from app.schemas.driver import DriverSummaryResponse


class DriverServiceClient:
    _DEV_FALLBACK_DRIVERS = [
        {
            "driver_id": 1,
            "driver_name": "Jordan Lee",
            "vehicle_type": "Van",
            "driver_status": "available",
        },
        {
            "driver_id": 2,
            "driver_name": "Sam Patel",
            "vehicle_type": "Bike",
            "driver_status": "available",
        },
        {
            "driver_id": 3,
            "driver_name": "Avery Chen",
            "vehicle_type": "Truck",
            "driver_status": "on_route",
        },
    ]

    def __init__(
        self,
        *,
        base_url: str | None = None,
        drivers_path: str | None = None,
        timeout_seconds: float | None = None,
        enable_dev_fallback: bool | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.base_url = (base_url or settings.driver_service_base_url).rstrip("/")
        self.drivers_path = drivers_path or settings.driver_service_drivers_path
        self.timeout_seconds = timeout_seconds or settings.driver_service_timeout_seconds
        self.enable_dev_fallback = (
            settings.driver_service_enable_dev_fallback
            if enable_dev_fallback is None
            else enable_dev_fallback
        )
        self._http_client = http_client
        self._driver_list_adapter = TypeAdapter(list[DriverSummaryResponse])

    def list_drivers(self) -> list[DriverSummaryResponse]:
        if self.enable_dev_fallback:
            return self._validate_driver_list(self._DEV_FALLBACK_DRIVERS)

        response = self._get(self._build_drivers_url())
        if response.status_code == 404:
            raise UpstreamNotFoundError("Driver Service driver roster endpoint was not found")
        if response.status_code >= 400:
            raise UpstreamBadResponseError(
                f"Driver Service returned HTTP {response.status_code} for driver roster lookup"
            )

        try:
            payload: Any = response.json()
        except ValueError as exc:
            raise UpstreamBadResponseError("Driver Service returned invalid JSON") from exc

        if isinstance(payload, dict) and "drivers" in payload:
            payload = payload["drivers"]

        return self._validate_driver_list(payload)

    def get_driver(self, driver_id: int) -> DriverSummaryResponse:
        for driver in self.list_drivers():
            if driver.driver_id == driver_id:
                return driver
        raise UpstreamNotFoundError(f"Driver {driver_id} was not found in Driver Service")

    def _validate_driver_list(self, payload: Any) -> list[DriverSummaryResponse]:
        try:
            return self._driver_list_adapter.validate_python(payload)
        except ValidationError as exc:
            raise UpstreamBadResponseError("Driver Service returned an invalid driver roster response") from exc

    def _build_drivers_url(self) -> str:
        return f"{self.base_url}{self.drivers_path}"

    def _get(self, url: str) -> httpx.Response:
        if self._http_client is not None:
            return self._request_with_client(self._http_client, url)

        with httpx.Client(timeout=self.timeout_seconds) as client:
            return self._request_with_client(client, url)

    def _request_with_client(self, client: httpx.Client, url: str) -> httpx.Response:
        try:
            return client.get(url)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError("Driver Service request timed out") from exc
        except httpx.HTTPError as exc:
            raise UpstreamBadResponseError("Driver Service request failed") from exc
