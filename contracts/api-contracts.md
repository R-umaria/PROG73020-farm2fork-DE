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
Loads an existing delivery request, fetches customer details from Customer & Subscriptions, geocodes the address, and saves the enrichment snapshot to Delivery Execution.

Success response (`200 OK`):
```json
{
  "message": "Customer details synced (v1)",
  "delivery_request_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
  "sync_status": "completed"
}
```

Error responses:
- `404 Not Found` when the delivery request does not exist or the upstream customer record cannot be found.
- `502 Bad Gateway` when the customer or geocoding dependency returns an invalid response payload.
- `504 Gateway Timeout` when the customer or geocoding dependency times out.

Notes:
- Customer sync persists both a flattened `CustomerDetails` record and a raw `CustomerDetailsSnapshot` payload.
- The current customer adapter expects an upstream payload shaped like:
  ```json
  {
    "customer_id": 501,
    "customer_name": "Jane Doe",
    "phone_number": "555-0101",
    "address": {
      "street": "123 Market Street",
      "city": "Toronto",
      "province": "ON",
      "postal_code": "M5V 1A1",
      "country": "CA"
    }
  }
  ```
- The current geocoding adapter expects an upstream payload shaped like:
  ```json
  {
    "latitude": 43.6532,
    "longitude": -79.3832
  }
  ```

## Planning backlog grouping contract (v1)
### `POST /api/planning/group-backlog`
Groups eligible delivery backlog deterministically for later scheduling. This endpoint does **not** create routes or assignments yet.

Success response (`200 OK`):
```json
{
  "message": "Backlog grouped deterministically (v1)",
  "total_groups": 3,
  "total_candidates": 4,
  "skipped_count": 2,
  "groups": [
    {
      "group_key": "delivery:postal_prefix:M5V",
      "handling_type": "delivery",
      "region_key": "postal_prefix:M5V",
      "region_source": "postal_prefix",
      "request_count": 2,
      "candidates": [
        {
          "delivery_request_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
          "order_id": 1001,
          "customer_id": 501,
          "handling_type": "delivery",
          "region_key": "postal_prefix:M5V",
          "region_source": "postal_prefix",
          "postal_prefix": "M5V",
          "city": "Toronto",
          "province": "ON",
          "request_timestamp": "2026-04-08T12:30:00Z"
        }
      ]
    }
  ],
  "skipped_requests": [
    {
      "delivery_request_id": "1a17d827-4e53-4b15-b90d-2df0b57fa0c5",
      "order_id": 1005,
      "reason": "missing_customer_enrichment"
    }
  ]
}
```

Eligibility rules:
- A request must not already be attached to a `RouteStop`.
- A request must have customer enrichment with non-empty street, city, province, and country fields.
- Region derivation uses postal prefix first. If no usable postal prefix exists, it falls back to normalized `city + province`.
- The grouping key includes handling type, so pickup requests stay separate from delivery requests when `order_type` is present in the intake snapshot.

Determinism rules:
- Group keys are sorted lexicographically.
- Candidates inside each group are sorted by `request_timestamp`, then `order_id`, then `delivery_request_id`.
- Postal prefixes are normalized by removing spaces/punctuation and taking the first three alphanumeric characters.

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
