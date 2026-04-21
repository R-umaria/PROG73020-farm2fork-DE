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
            return self._normalize_customer_record(payload, requested_customer_id=customer_id)
        except (ValidationError, ValueError, TypeError) as exc:
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

    @classmethod
    def _normalize_customer_record(cls, payload: Any, *, requested_customer_id: int) -> CustomerRecord:
        if not isinstance(payload, dict):
            raise ValueError("Customer payload must be an object")

        customer_id = cls._coerce_int(
            payload.get("customer_id")
            or payload.get("customerId")
            or payload.get("id")
            or requested_customer_id
        )

        customer_name = cls._coerce_text(
            payload.get("customer_name")
            or payload.get("customerName")
            or payload.get("name")
            or payload.get("full_name")
        )
        phone_number = cls._coerce_text(
            payload.get("phone_number")
            or payload.get("phoneNumber")
            or payload.get("phone")
            or payload.get("mobile")
            or payload.get("mobile_number")
        )

        address_payload = cls._extract_address_payload(payload)
        address = CustomerAddress.model_validate(address_payload)
        return CustomerRecord(
            customer_id=customer_id,
            customer_name=customer_name,
            phone_number=phone_number,
            address=address,
        )

    @classmethod
    def _extract_address_payload(cls, payload: dict[str, Any]) -> dict[str, Any]:
        address = payload.get("address")
        if not isinstance(address, dict):
            address = payload.get("default_delivery_address")
        if not isinstance(address, dict):
            address = payload.get("defaultDeliveryAddress")
        if not isinstance(address, dict):
            address = payload.get("delivery_address")
        if not isinstance(address, dict):
            address = payload.get("deliveryAddress")
        if not isinstance(address, dict):
            address = payload

        address_text = payload.get("address") if isinstance(payload.get("address"), str) else None
        street = cls._coerce_text(
            address.get("street")
            or address.get("street1")
            or address.get("street_1")
            or address.get("address1")
            or address.get("address_line_1")
            or address.get("line1")
            or payload.get("street")
            or address_text
        )

        city = cls._coerce_text(
            address.get("city")
            or payload.get("city")
        )
        province = cls._coerce_text(
            address.get("province")
            or address.get("state")
            or address.get("region")
            or payload.get("province")
            or payload.get("state")
        )
        postal_code = cls._coerce_text(
            address.get("postal_code")
            or address.get("postalCode")
            or address.get("zip")
            or address.get("zip_code")
            or address.get("zipCode")
            or payload.get("postal_code")
            or payload.get("postalCode")
        )
        country = cls._coerce_text(
            address.get("country")
            or address.get("country_code")
            or payload.get("country")
            or payload.get("country_code")
            or settings.geocoding_default_country
        )

        return {
            "street": street,
            "city": city,
            "province": province,
            "postal_code": postal_code,
            "country": country,
        }

    @staticmethod
    def _coerce_text(value: Any) -> str:
        if value is None:
            return ""
        return " ".join(str(value).strip().split())

    @staticmethod
    def _coerce_int(value: Any) -> int:
        return int(value)
