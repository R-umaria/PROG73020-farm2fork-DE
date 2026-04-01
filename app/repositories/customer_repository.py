from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.db_models import (
    CustomerDetails,
    CustomerDetailsSnapshot,
)


class CustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_customer_enrichment(
        self,
        *,
        delivery_request_id: UUID,
        raw_payload: dict[str, Any],
        customer_name: str,
        phone_number: str,
        street: str,
        city: str,
        province: str,
        postal_code: str,
        country: str,
        latitude=None,
        longitude=None,
        geocode_status: str | None = None,
    ) -> CustomerDetails:
        snapshot = CustomerDetailsSnapshot(
            delivery_request_id=delivery_request_id,
            customer_payload=raw_payload,
        )
        self.db.add(snapshot)

        customer_details = CustomerDetails(
            delivery_request_id=delivery_request_id,
            customer_name=customer_name,
            phone_number=phone_number,
            street=street,
            city=city,
            province=province,
            postal_code=postal_code,
            country=country,
            latitude=latitude,
            longitude=longitude,
            geocode_status=geocode_status,
        )
        self.db.add(customer_details)

        self.db.commit()
        self.db.refresh(customer_details)
        return customer_details

    def get_by_delivery_request_id(self, delivery_request_id: UUID) -> CustomerDetails | None:
        return (
            self.db.query(CustomerDetails)
            .filter(CustomerDetails.delivery_request_id == delivery_request_id)
            .first()
        )