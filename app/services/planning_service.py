from __future__ import annotations

import re
from collections import defaultdict
from typing import Literal

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.repositories.planning_repository import PlanningRepository
from app.schemas.planning import (
    BacklogPlanningCandidate,
    BacklogPlanningGroup,
    BacklogPlanningSkip,
    GroupBacklogResponse,
)

RegionSource = Literal["postal_prefix", "city_province"]
HandlingType = Literal["delivery", "pickup"]


class PlanningService:
    def __init__(self, db: Session | None = None):
        self.db: Session = db or SessionLocal()
        self.repo = PlanningRepository(self.db)

    def geocode_pending_requests(self):
        return {"message": "Pending addresses geocoded placeholder"}

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

    def schedule_routes(self):
        return {"message": "Route scheduling placeholder"}

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

        if isinstance(order_type, str) and order_type.strip().lower() == "pickup":
            return "pickup"

        return "delivery"

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
