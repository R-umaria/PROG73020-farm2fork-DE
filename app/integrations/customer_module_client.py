"""Customer module adapter with timeout handling and response validation."""

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


class CustomerAddress(BaseModel):
    model_config = ConfigDict(extra="ignore")

    street: str
    city: str
    province: str
    postal_code: str
    country: str


class CustomerRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")

    customer_id: int
    customer_name: str
    phone_number: str
    address: CustomerAddress


class CustomerModuleClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        customer_lookup_path: str | None = None,
        timeout_seconds: float | None = None,
        http_client: httpx.Client | None = None,
    ):
        self.base_url = (base_url or settings.customer_module_base_url).rstrip("/")
        self.customer_lookup_path = customer_lookup_path or settings.customer_module_customer_lookup_path
        self.timeout_seconds = timeout_seconds or settings.customer_module_timeout_seconds
        self._http_client = http_client

    def get_customer_details(self, customer_id: int) -> CustomerRecord:
        response = self._get(self._build_url(customer_id))

        if response.status_code == 404:
            raise UpstreamNotFoundError(f"Customer {customer_id} was not found in Customer & Subscriptions")

        if response.status_code >= 400:
            raise UpstreamBadResponseError(
                f"Customer & Subscriptions returned HTTP {response.status_code} for customer {customer_id}"
            )

        try:
            payload: Any = response.json()
        except ValueError as exc:
            raise UpstreamBadResponseError("Customer & Subscriptions returned invalid JSON") from exc

        try:
            return CustomerRecord.model_validate(payload)
        except ValidationError as exc:
            raise UpstreamBadResponseError(
                "Customer & Subscriptions returned an invalid customer response"
            ) from exc

    def _build_url(self, customer_id: int) -> str:
        path = self.customer_lookup_path.format(customer_id=customer_id)
        return f"{self.base_url}{path}"

    def _get(self, url: str) -> httpx.Response:
        if self._http_client is not None:
            return self._request_with_client(self._http_client, url)

        with httpx.Client(timeout=self.timeout_seconds) as client:
            return self._request_with_client(client, url)

    def _request_with_client(self, client: httpx.Client, url: str) -> httpx.Response:
        try:
            return client.get(url)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError("Customer & Subscriptions request timed out") from exc
        except httpx.HTTPError as exc:
            raise UpstreamBadResponseError("Customer & Subscriptions request failed") from exc
