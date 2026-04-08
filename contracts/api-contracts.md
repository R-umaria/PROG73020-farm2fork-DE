# API Contracts

Keep this file updated whenever request/response shapes change.

## Current planned endpoints
- `POST /api/delivery-requests/`
- `POST /api/delivery-requests/{delivery_request_id}/customer-sync`
- `POST /api/planning/geocode-pending`
- `POST /api/planning/group-backlog`
- `POST /api/planning/schedule`
- `GET /api/delivery-status/{order_id}`
- `GET /api/driver/schedule/today/{driver_id}`
- `POST /api/driver/start-day/{driver_id}`
- `POST /api/driver/stops/{route_stop_id}/complete`
- `POST /api/deliveries/{delivery_execution_id}/start`
- `POST /api/deliveries/{delivery_execution_id}/complete`
- `POST /api/deliveries/{delivery_execution_id}/fail`

## Delivery execution status values
All delivery execution APIs must use these canonical values:
- `scheduled`
- `out_for_delivery`
- `delivered`
- `failed`

## Delivery action transition behavior
- Delivery action endpoints return `409 Conflict` when a requested status change violates the allowed delivery execution transitions.
