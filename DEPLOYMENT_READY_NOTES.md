# Deployment-ready notes

## Intake routes that accept Order Orchestration payloads
- `POST /api/delivery-requests/`
- `POST /api/delivery-requests/manifest`
- `POST /api/delivery-requests/order-manifest`

All three accept either the original snake_case contract or the Order Orchestration sample payload using:
- `orderId`
- `customerID`
- `timestamp`
- `pickup`
- item fields like `id`, `name`, `quantity`

## Customer & Subscriptions integration defaults
The service is preconfigured to call:
- base URL: `http://159.203.16.186:3000`
- customer lookup path: `/customers/{customer_id}`

The customer adapter is tolerant to multiple response shapes, including nested delivery-address variants.

## Deployment defaults changed from demo mode
- `DEMO_DATA_AUTO_SEED=false`
- `DRIVER_SERVICE_ENABLE_DEV_FALLBACK=false`
- `INTAKE_AUTO_SYNC_CUSTOMER=true`
- `INTAKE_AUTO_SCHEDULE=true`
- `PLANNING_DRIVER_COUNT=100`
- `PLANNING_TRUCK_COUNT=100`
- `PLANNING_MAX_ORDERS_PER_ROUTE=50`
- `PLANNING_AUTO_ASSIGN_DRIVERS=false`

## Scheduling behavior
- pickup orders become `ready_for_pickup`
- delivery orders auto-sync customer details and auto-enter scheduling
- routes are chunked at 50 orders max per route group
- route groups are scheduled against weekday 9–5 business capacity using a 100-driver / 100-truck assumption
- shifts remain claimable by drivers because automatic pre-assignment is disabled by default

## Frontend deployment behavior
If `NEXT_PUBLIC_API_BASE_URL` is left blank, the driver portal infers the backend API as the same host on port `8000`.
Example:
- frontend: `http://YOUR_SERVER_IP:3000`
- backend inferred: `http://YOUR_SERVER_IP:8000`
