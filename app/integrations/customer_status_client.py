from __future__ import annotations

from dataclasses import dataclass
import requests
from app.core.config import settings


@dataclass(slots=True)
class CustomerStatusSyncResult:
    status: str
    updated_count: int


class CustomerStatusClient:
    def __init__(self) -> None:
        self.enabled = settings.customer_status_callback_enabled and bool(settings.customer_status_callback_base_url.strip())
        self.base_url = settings.customer_status_callback_base_url.rstrip('/')
        self.path_template = settings.customer_status_callback_path
        self.timeout_seconds = settings.customer_status_callback_timeout_seconds

    def notify_orders_dispatched(self, order_ids: list[int]) -> CustomerStatusSyncResult:
        if not order_ids:
            return CustomerStatusSyncResult(status='no_orders', updated_count=0)
        if not self.enabled:
            return CustomerStatusSyncResult(status='not_configured', updated_count=len(order_ids))
        updated = 0
        for order_id in order_ids:
            url = f"{self.base_url}{self.path_template.format(order_id=order_id)}"
            response = requests.post(url, json={'status': 'dispatched', 'source': 'delivery_execution', 'order_id': order_id}, timeout=self.timeout_seconds)
            response.raise_for_status(); updated += 1
        return CustomerStatusSyncResult(status='sent', updated_count=updated)
