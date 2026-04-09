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

## Planning route scheduling contract (v1)
### `POST /api/planning/schedule`
Creates `RouteGroup` and `RouteStop` records from the current eligible grouped backlog, then applies the default deterministic driver-assignment heuristic.

Success response (`200 OK`):
```json
{
  "message": "Route groups scheduled deterministically (v1)",
  "scheduled_group_count": 2,
  "assigned_group_count": 2,
  "unassigned_group_count": 0,
  "route_groups": [
    {
      "route_group_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
      "group_key": "delivery:postal_prefix:M5V",
      "route_group_name": "route-group:delivery:postal_prefix:M5V:20260408T123000Z",
      "handling_type": "delivery",
      "zone_code": "postal_prefix:M5V",
      "scheduled_date": "2026-04-08T12:30:00Z",
      "route_group_status": "scheduled",
      "total_stops": 2,
      "driver_assignment": {
        "driver_id": 2,
        "driver_name": "Sam Patel",
        "vehicle_type": "Bike",
        "driver_status": "available",
        "assignment_status": "assigned",
        "current_load_before_assignment": 0
      },
      "stops": [
        {
          "route_stop_id": "1a17d827-4e53-4b15-b90d-2df0b57fa0c5",
          "delivery_request_id": "3f157fb6-140f-4c25-a2e7-42daf4f35e13",
          "order_id": 1001,
          "sequence": 1,
          "stop_status": "planned",
          "estimated_arrival": "2026-04-08T12:30:00Z"
        }
      ]
    }
  ]
}
```

Scheduling rules:
- One route group is created for each grouped backlog partition.
- Route-group scheduling uses the earliest candidate `request_timestamp` in the group.
- Route-stop sequence reuses the deterministic grouped candidate order.
- Simple estimated arrivals are produced in 15-minute increments for sequencing only.

Driver assignment rules:
- Only drivers with status `available` are eligible.
- The default policy prefers lower current active assignment load.
- Ties are broken deterministically by `driver_id`, then driver name.
- If no available driver exists, the route group is still created and returned without a `driver_assignment`.

## Tracking status contract (v1)
### `GET /api/delivery-status/{order_id}`
Returns the persisted delivery execution read model for a scheduled or active order.

Success response (`200 OK`):
```json
{
  "order_id": 1001,
  "customer_id": 501,
  "delivery_request_id": "3f157fb6-140f-4c25-a2e7-42daf4f35e13",
  "delivery_execution_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
  "delivery_status": "out_for_delivery",
  "latest_status_at": "2026-04-08T13:00:00Z",
  "latest_status_reason": "Driver started route",
  "route_group_id": "14bfdc2d-cf59-4fb1-bd59-7a89e1116af0",
  "route_group_status": "scheduled",
  "route_stop_id": "1a17d827-4e53-4b15-b90d-2df0b57fa0c5",
  "stop_sequence": 1,
  "stop_status": "planned",
  "estimated_arrival": "2026-04-08T12:30:00Z",
  "assigned_driver_id": 2,
  "assignment_status": "assigned",
  "dispatched_at": "2026-04-08T13:00:00Z",
  "out_for_delivery_at": "2026-04-08T13:00:00Z",
  "status_history": [
    {
      "status": "scheduled",
      "changed_at": "2026-04-08T12:30:00Z",
      "changed_by": "system",
      "reason": "Initial execution record created"
    },
    {
      "status": "out_for_delivery",
      "changed_at": "2026-04-08T13:00:00Z",
      "changed_by": "driver",
      "reason": "Driver started route"
    }
  ]
}
```

Not found response (`404 Not Found`):
```json
{
  "detail": "Tracked delivery status not found for order_id 1001"
}
```

Notes:
- The tracking source of truth is the persisted `DeliveryExecution` aggregate plus `StatusHistory` timeline.
- Orders without a created execution record are not yet trackable and return `404`.
- Scheduling creates the initial `scheduled` execution record; later execution actions append history entries and internal event records.
- `route_group_id`, `route_stop_id`, `estimated_arrival`, and `assigned_driver_id` are included when planning data already exists.

## Driver roster and driver portal contracts (v1)
### Upstream Driver Service roster dependency
The current adapter expects the upstream Driver Service roster payload to be either a bare array or an envelope with a `drivers` field using this shape:

```json
{
  "drivers": [
    {
      "driver_id": 2,
      "driver_name": "Sam Patel",
      "vehicle_type": "Bike",
      "driver_status": "available"
    }
  ]
}
```

Error handling:
- `404` when the upstream roster endpoint or requested driver cannot be found.
- `502` when the upstream payload is invalid or unusable.
- `504` when the upstream request times out.

Development fallback note:
- A local fallback roster exists only when `driver_service_enable_dev_fallback=true` is explicitly enabled in settings.
- Production-style paths must not silently fake driver data.

### `GET /api/drivers/`
Primary driver roster route. Returns the explicit v1 driver contract projected from Driver Service.

Response body:
```json
[
  {
    "driver_id": 2,
    "driver_name": "Sam Patel",
    "vehicle_type": "Bike",
    "driver_status": "available"
  }
]
```

### `GET /api/driver/`
Compatibility alias for `GET /api/drivers/`. Existing consumers may continue to use it, but new consumers should prefer the plural collection path.

### `GET /api/driver/schedule/today/{driver_id}`
Returns the current local route-stop view for a driver, combined with upstream driver roster data.

Response body:
```json
{
  "driver_id": 2,
  "driver_name": "Sam Patel",
  "vehicle_type": "Bike",
  "driver_status": "available",
  "stops": [
    {
      "route_stop_id": "1a17d827-4e53-4b15-b90d-2df0b57fa0c5",
      "route_group_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
      "delivery_request_id": "3f157fb6-140f-4c25-a2e7-42daf4f35e13",
      "order_id": 1001,
      "sequence": 1,
      "stop_status": "planned",
      "estimated_arrival": "2026-04-08T12:30:00Z",
      "address": "123 Market Street, Toronto, ON, M5V 1A1, CA"
    }
  ]
}
```

### `POST /api/driver/start-day/{driver_id}`
Lightweight acknowledgement route using the same driver field names as the roster and schedule contracts.

Response body:
```json
{
  "driver_id": 2,
  "driver_name": "Sam Patel",
  "driver_status": "available",
  "message": "Driver day started (v1)"
}
```

### `POST /api/driver/stops/{route_stop_id}/complete`
Marks the local route stop record complete without changing the delivery execution status model.

Response body:
```json
{
  "route_stop_id": "1a17d827-4e53-4b15-b90d-2df0b57fa0c5",
  "stop_status": "completed",
  "message": "Route stop marked completed (v1)"
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
  "updated_at": "2026-04-08T12:30:05Z",
  "customer_details": {
    "customer_name": "Jane Doe",
    "phone_number": "555-0101",
    "street": "123 Market Street",
    "city": "Toronto",
    "province": "ON",
    "postal_code": "M5V 1A1",
    "country": "CA",
    "latitude": 43.6532,
    "longitude": -79.3832,
    "geocode_status": "completed"
  }
}
```

### `GET /api/deliveries/`
Returns a list of `DeliveryRequest` records using the same response shape as above.

### `GET /api/deliveries/{delivery_id}`
Returns one `DeliveryRequest` record by UUID.

Notes:
- `customer_details` is optional and appears after customer-sync enrichment has been completed.
- The connected driver portal uses this additive field to show customer name, phone, and address details without introducing a new read endpoint.

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
