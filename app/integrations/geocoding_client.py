"""Geocoding adapter with timeout handling and response validation."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.config import settings
from app.integrations.errors import (
    UpstreamBadResponseError,
    UpstreamNotFoundError,
    UpstreamTimeoutError,
)


class GeocodeResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    latitude: float
    longitude: float


class GeocodingClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        geocode_path: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.base_url = (base_url or settings.geocoding_base_url).rstrip("/")
        self.geocode_path = geocode_path or settings.geocoding_lookup_path
        self.timeout_seconds = timeout_seconds or settings.geocoding_timeout_seconds
        self._http_client = http_client

    def geocode_address(
        self,
        *,
        street: str,
        city: str,
        province: str,
        postal_code: str,
        country: str,
    ) -> GeocodeResult:
        response = self._get(
            self._build_url(),
            params={
                "street": street,
                "city": city,
                "province": province,
                "postal_code": postal_code,
                "country": country,
            },
        )

        if response.status_code == 404:
            raise UpstreamNotFoundError("Geocoding service could not resolve the customer address")

        if response.status_code >= 400:
            raise UpstreamBadResponseError(
                f"Geocoding service returned HTTP {response.status_code}"
            )

        try:
            payload: Any = response.json()
        except ValueError as exc:
            raise UpstreamBadResponseError("Geocoding service returned invalid JSON") from exc

        try:
            return GeocodeResult.model_validate(payload)
        except ValidationError as exc:
            raise UpstreamBadResponseError("Geocoding service returned an invalid geocode response") from exc

    def _build_url(self) -> str:
        return f"{self.base_url}{self.geocode_path}"

    def _get(self, url: str, *, params: dict[str, str]) -> httpx.Response:
        if self._http_client is not None:
            return self._request_with_client(self._http_client, url, params=params)

        with httpx.Client(timeout=self.timeout_seconds) as client:
            return self._request_with_client(client, url, params=params)

    def _request_with_client(self, client: httpx.Client, url: str, *, params: dict[str, str]) -> httpx.Response:
        try:
            return client.get(url, params=params)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError("Geocoding service request timed out") from exc
        except httpx.HTTPError as exc:
            raise UpstreamBadResponseError("Geocoding service request failed") from exc
