"""Persistence helpers for the lightweight internal event outbox.

The repo keeps event generation explicit and queryable without introducing a
full messaging stack at this stage of the project.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.db_models import InternalEventRecord


_EVENT_ORDER = {
    "DeliveryScheduled": 0,
    "DeliveryDispatched": 1,
    "DeliveryCompleted": 2,
    "DeliveryFailed": 3,
}


class EventRepository:
    """Stores internal event records that stand in for future bus publishing."""

    def __init__(self, db: Session):
        self.db = db

    def record_event(
        self,
        *,
        aggregate_type: str,
        aggregate_id: UUID,
        event_type: str,
        event_payload: dict[str, Any],
        order_id: int | None = None,
    ) -> InternalEventRecord:
        event_record = InternalEventRecord(
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_type=event_type,
            order_id=order_id,
            event_payload=event_payload,
        )
        self.db.add(event_record)
        return event_record

    def list_events(self) -> list[InternalEventRecord]:
        records = self.db.query(InternalEventRecord).all()
        return sorted(
            records,
            key=lambda event: (event.occurred_at, _EVENT_ORDER.get(event.event_type, 99)),
        )
