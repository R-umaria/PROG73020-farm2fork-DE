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
- The raw inbound payload is persisted as a delivery request snapshot for traceability and duplicate comparison.
- Customer address/contact enrichment remains outside this payload until customer sync is implemented.
- Duplicate handling is keyed by `order_id`: the same payload is idempotent, while a conflicting payload for the same `order_id` is rejected.

## Delivery status read model (v1)
Current DB-backed tracking payload shape:

```json
{
  "order_id": 1001,
  "customer_id": 501,
  "delivery_request_id": "3f157fb6-140f-4c25-a2e7-42daf4f35e13",
  "delivery_execution_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
  "delivery_status": "scheduled",
  "latest_status_at": "2026-04-08T12:30:00Z",
  "route_group_id": "14bfdc2d-cf59-4fb1-bd59-7a89e1116af0",
  "route_stop_id": "1a17d827-4e53-4b15-b90d-2df0b57fa0c5",
  "estimated_arrival": "2026-04-08T12:30:00Z",
  "assigned_driver_id": 2,
  "status_history": [
    {
      "status": "scheduled",
      "changed_at": "2026-04-08T12:30:00Z",
      "changed_by": "system",
      "reason": "Initial execution record created"
    }
  ]
}
```

## Canonical delivery execution status vocabulary
- `scheduled`
- `out_for_delivery`
- `delivered`
- `failed`

## Event emission semantics (v1)
The repo does not publish to Kafka/RabbitMQ/etc. yet. Instead, it persists explicit internal event records in `internal_event_record` using the payload shape below. This acts as an outbox-style placeholder so event generation points remain visible and testable.

Shared payload shape:

```json
{
  "event_version": "v1",
  "order_id": 1001,
  "delivery_request_id": "3f157fb6-140f-4c25-a2e7-42daf4f35e13",
  "delivery_execution_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
  "delivery_status": "scheduled",
  "previous_status": null,
  "changed_by": "system",
  "reason": "Initial execution record created",
  "route_group_id": "14bfdc2d-cf59-4fb1-bd59-7a89e1116af0",
  "route_group_status": "scheduled",
  "route_stop_id": "1a17d827-4e53-4b15-b90d-2df0b57fa0c5",
  "stop_sequence": 1,
  "stop_status": "planned",
  "estimated_arrival": "2026-04-08T12:30:00Z",
  "driver_id": 2,
  "assignment_status": "assigned"
}
```

### `DeliveryScheduled`
Emitted exactly once per delivery request when planning persists the initial `DeliveryExecution` record in the canonical `scheduled` state.

Generation point:
- `PlanningService.schedule_routes()` creates `RouteGroup` and `RouteStop` records.
- Immediately after the stop exists, `ExecutionRepository.create_execution(...)` persists the execution aggregate.
- The internal event record is written in the same repository flow before commit.

### `DeliveryDispatched`
Emitted when the execution transition `scheduled -> out_for_delivery` is persisted.

Generation point:
- `DeliveryActionsService.start_delivery(...)`
- `ExecutionRepository.update_status(...)`

Semantics:
- `dispatched_at` and `out_for_delivery_at` are set when this transition is recorded.
- This is the execution-layer equivalent of the driver starting the route for the stop/order.

### `DeliveryCompleted`
Emitted when the execution transition `out_for_delivery -> delivered` is persisted.

Generation point:
- `DeliveryActionsService.complete_delivery(...)`
- `ExecutionRepository.update_status(...)`

Semantics:
- The event is keyed to the persisted status transition itself.
- Delivery confirmation persistence happens in the same API action afterward, but confirmation is not the gating condition for event emission.

### `DeliveryFailed`
Emitted when the execution transition to `failed` is persisted from an allowed prior state.

Generation point:
- `DeliveryActionsService.fail_delivery(...)`
- `ExecutionRepository.update_status(...)`

Semantics:
- Exception persistence happens in the same API action afterward, but the event is keyed to the canonical status transition.
- `failed` remains a terminal state in the current implementation.

## Allowed transitions
- `scheduled` → `out_for_delivery`
- `scheduled` → `failed`
- `out_for_delivery` → `delivered`
- `out_for_delivery` → `failed`
- `delivered` and `failed` are terminal for the current implementation

## DriverAssigned (v1)
Current planning/read-model shape for a route-group driver assignment:

```json
{
  "route_group_id": "2ec537a9-8b7e-4fe9-981a-823f670f12d0",
  "driver_assignment": {
    "driver_id": 2,
    "driver_name": "Sam Patel",
    "vehicle_type": "Bike",
    "driver_status": "available",
    "assignment_status": "assigned",
    "current_load_before_assignment": 0
  }
}
```

Notes:
- Driver field names intentionally match the upstream Driver Service roster contract.
- `assignment_status` belongs to Delivery Execution and remains distinct from upstream `driver_status`.
- Route-stop `stop_status` remains distinct from delivery execution status transitions.
