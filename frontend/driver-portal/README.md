# Farm2Fork Driver Portal

This Next.js app is the connected driver portal for the Delivery Execution backend.

## What is wired right now
- backend-linked driver sign-in using the live `/api/drivers/` roster
- browser session/local storage for the selected driver session
- live dashboard data from `/api/driver/schedule/today/{driver_id}`
- live delivery detail views using `/api/deliveries/{delivery_request_id}` and `/api/delivery-status/{order_id}`
- delivery actions using:
  - `POST /api/deliveries/{delivery_execution_id}/start`
  - `POST /api/deliveries/{delivery_execution_id}/complete`
  - `POST /api/deliveries/{delivery_execution_id}/fail`
  - `POST /api/driver/stops/{route_stop_id}/complete`

## Local setup
### 1) Start the backend
```bash
cp .env.example .env
```

For a local demo without a separate Driver Service, enable the explicit development fallback:
```bash
DRIVER_SERVICE_ENABLE_DEV_FALLBACK=true
```

Then run the backend:
```bash
docker compose up --build
```

### 2) Start the driver portal
```bash
cd frontend/driver-portal
cp .env.example .env.local
npm install
npm run dev
```

## Environment
The frontend reads this value from `.env.local`:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## URLs
- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`
- Driver portal: `http://localhost:3000`

## Notes
- The backend now allows browser calls from `http://localhost:3000` by default.
- This portal intentionally does **not** use JWT/OAuth yet. It stores the selected driver session in browser storage for demo purposes.
