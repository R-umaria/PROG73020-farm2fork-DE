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
        snapshot = (
            self.db.query(CustomerDetailsSnapshot)
            .filter(CustomerDetailsSnapshot.delivery_request_id == delivery_request_id)
            .first()
        )
        if snapshot is None:
            snapshot = CustomerDetailsSnapshot(
                delivery_request_id=delivery_request_id,
                customer_payload=raw_payload,
            )
            self.db.add(snapshot)
        else:
            snapshot.customer_payload = raw_payload

        customer_details = self.get_by_delivery_request_id(delivery_request_id)
        if customer_details is None:
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
        else:
            customer_details.customer_name = customer_name
            customer_details.phone_number = phone_number
            customer_details.street = street
            customer_details.city = city
            customer_details.province = province
            customer_details.postal_code = postal_code
            customer_details.country = country
            customer_details.latitude = latitude
            customer_details.longitude = longitude
            customer_details.geocode_status = geocode_status

        self.db.commit()
        self.db.refresh(customer_details)
        return customer_details

    def get_by_delivery_request_id(self, delivery_request_id: UUID) -> CustomerDetails | None:
        return (
            self.db.query(CustomerDetails)
            .filter(CustomerDetails.delivery_request_id == delivery_request_id)
            .first()
        )
