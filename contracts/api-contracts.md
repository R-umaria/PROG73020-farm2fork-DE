# API Contracts

Keep this file updated whenever request/response shapes change.

## Versioning note
The routes remain under the existing `/api` path structure. The request and response shapes documented below are the explicit **v1** contracts.

## Primary intake contract (v1)
### `POST /api/delivery-requests/`
Primary inbound contract for Delivery Execution.

Request body:
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

Response body on first create (`201 Created`):
```json
{
  "message": "Delivery request persisted (v1)",
  "order_id": 1001,
  "request_status": "received",
  "delivery_request_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0"
}
```

Response body on idempotent duplicate with the same payload (`200 OK`):
```json
{
  "message": "Delivery request already received (v1)",
  "order_id": 1001,
  "request_status": "received",
  "delivery_request_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0"
}
```

Conflicting duplicate response (`409 Conflict`):
```json
{
  "detail": "Conflicting delivery request already exists for order_id 1001"
}
```

Notes:
- Intake now persists the `DeliveryRequest` record, the raw request snapshot, and child `DeliveryItem` rows.
- Idempotency is keyed on `order_id`.
- Repeating the same payload for the same `order_id` returns the existing `delivery_request_id` without overwriting persisted data.
- Repeating a different payload for the same `order_id` is rejected with `409 Conflict`.
- `request_status` reflects the Delivery Execution intake/request record, not the delivery execution status model.
- `request_timestamp` must include a timezone offset.

### `POST /api/delivery-requests/{delivery_request_id}/customer-sync`
Placeholder contract for customer data sync linked to an existing delivery request record.

Response body:
```json
{
  "message": "Customer details sync placeholder",
  "delivery_request_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
  "sync_status": "placeholder"
}
```

## Manual/non-primary delivery record route (v1)
### `POST /api/deliveries/`
Non-primary manual creation path. This persists a `DeliveryRequest` record using the same v1 payload shape as intake, but it is not the canonical idempotent intake path.
Prefer `POST /api/delivery-requests/` for the primary intake contract and duplicate-handling behavior.

Request body:
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

Response body:
```json
{
  "id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
  "order_id": 1001,
  "customer_id": 501,
  "request_timestamp": "2026-04-08T12:30:00Z",
  "items": [
    {
      "external_item_id": 9001,
      "item_name": "Mixed Farm Box",
      "quantity": 1
    }
  ],
  "request_status": "received",
  "created_at": "2026-04-08T12:30:05Z",
  "updated_at": "2026-04-08T12:30:05Z"
}
```

### `GET /api/deliveries/`
Returns a list of `DeliveryRequest` records using the same response shape as above.

### `GET /api/deliveries/{delivery_id}`
Returns one `DeliveryRequest` record by UUID.

## Tracking contract (v1)
### `GET /api/delivery-status/{order_id}`
Returns delivery execution status by numeric `order_id`.

Response body:
```json
{
  "order_id": 1001,
  "delivery_status": "scheduled"
}
```

`delivery_execution_id` may be included when the lookup path is backed by persisted execution records.

## Delivery action endpoints
### `POST /api/deliveries/{delivery_execution_id}/start`
### `POST /api/deliveries/{delivery_execution_id}/complete`
### `POST /api/deliveries/{delivery_execution_id}/fail`
These routes operate on `delivery_execution_id` and use the canonical delivery execution status model.

## Canonical delivery execution status values
All delivery execution APIs must use these canonical values:
- `scheduled`
- `out_for_delivery`
- `delivered`
- `failed`

## Delivery action transition behavior
- Delivery action endpoints return `409 Conflict` when a requested status change violates the allowed delivery execution transitions.
