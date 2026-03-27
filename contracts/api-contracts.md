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
