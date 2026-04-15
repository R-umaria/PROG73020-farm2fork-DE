from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

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
    display_name: str | None = None


class GeocodingClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        geocode_path: str | None = None,
        timeout_seconds: float | None = None,
        user_agent: str | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.base_url = (base_url or settings.geocoding_base_url).rstrip("/")
        self.geocode_path = geocode_path or settings.geocoding_lookup_path
        self.timeout_seconds = timeout_seconds or settings.geocoding_timeout_seconds
        self.user_agent = user_agent or settings.geocoding_user_agent
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
        params = {
            "street": street,
            "city": city,
            "state": province,
            "postalcode": postal_code,
            "country": country or settings.geocoding_default_country,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        }

        response = self._get(self._build_url(), params=params)

        if response.status_code >= 400:
            raise UpstreamBadResponseError(
                f"Geocoding service returned HTTP {response.status_code}"
            )

        try:
            payload: Any = response.json()
        except ValueError as exc:
            raise UpstreamBadResponseError("Geocoding service returned invalid JSON") from exc

        if not isinstance(payload, list) or not payload:
            raise UpstreamNotFoundError("Geocoding service could not resolve the customer address")

        first = payload[0]

        try:
            return GeocodeResult(
                latitude=float(first["lat"]),
                longitude=float(first["lon"]),
                display_name=first.get("display_name"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise UpstreamBadResponseError("Geocoding service returned an invalid geocode response") from exc

    def _build_url(self) -> str:
        return f"{self.base_url}{self.geocode_path}"

    def _get(self, url: str, *, params: dict[str, str]) -> httpx.Response:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        if self._http_client is not None:
            return self._request_with_client(self._http_client, url, params=params, headers=headers)

        with httpx.Client(timeout=self.timeout_seconds, headers=headers) as client:
            return self._request_with_client(client, url, params=params, headers=headers)

    def _request_with_client(
        self,
        client: httpx.Client,
        url: str,
        *,
        params: dict[str, str],
        headers: dict[str, str],
    ) -> httpx.Response:
        try:
            return client.get(url, params=params, headers=headers)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError("Geocoding service request timed out") from exc
        except httpx.HTTPError as exc:
            raise UpstreamBadResponseError("Geocoding service request failed") from exc