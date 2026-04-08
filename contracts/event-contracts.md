# Event Contracts

Track important state changes here.

## Versioning note
The event payloads below describe the explicit **v1** contracts aligned to the current Delivery Execution data model.

## DeliveryRequested (v1)
Inbound event/payload shape represented by the delivery request snapshot:

```json
{
  "order_id": 1001,
  "customer_id": 501,
  "request_timestamp": "2026-04-08T12:30:00Z",
  "items": [
    {
      "external_item_id": 9001,
      "item_name": "Mixed Farm Box",
      "quantity": 1
    }
  ]
}
```

Notes:
- This aligns to the current `DeliveryRequest` aggregate root and `DeliveryItem` child records.
- Customer address/contact enrichment remains outside this payload until customer sync is implemented.

## DeliveryStatusUpdated (v1)
Current tracking/status payload shape:

```json
{
  "order_id": 1001,
  "delivery_status": "scheduled"
}
```

`delivery_execution_id` may be added to the emitted/read-model payload when the tracking path is backed by persisted execution lookups.

## Canonical delivery execution status vocabulary
- `scheduled`
- `out_for_delivery`
- `delivered`
- `failed`

## Current event/state flow
1. `DeliveryScheduled` → execution enters `scheduled`
2. `DeliveryOutForDelivery` → execution transitions to `out_for_delivery`
3. `DeliveryDelivered` → execution transitions to `delivered`
4. `DeliveryFailed` → execution transitions to `failed`

## Allowed transitions
- `scheduled` → `out_for_delivery`
- `scheduled` → `failed`
- `out_for_delivery` → `delivered`
- `out_for_delivery` → `failed`
- `delivered` and `failed` are terminal for the current implementation
