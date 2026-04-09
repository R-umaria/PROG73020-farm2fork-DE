# Farm2Fork Delivery Execution

A simple shared repo for the Delivery Execution team.

## Why this structure
This layout is organized by the real workstreams of the module:
- **intake**: receive order data from Order Orchestration
- **planning**: geocoding, grouping, scheduling, route planning
- **tracking**: customer-facing delivery status lookup
- **driver**: driver schedule, start day, complete stop, driver UI
- **integrations**: external API clients for other teams/services

This keeps merge conflicts lower because teammates can mostly work in separate areas.

## Repo tree
```text
.
├── .github/
│   └── workflows/
├── adr/
├── alembic/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── integrations/
│   ├── models/
│   ├── repositories/
│   ├── schemas/
│   └── services/
├── contracts/
├── driver_ui/
│   ├── static/
│   └── templates/
└── tests/
    ├── api/
    └── services/
```

## Suggested ownership map
- **Rishi**: `contracts/`, `adr/`, `app/api/router.py`, architecture review of cross-area changes
- **Krishi**: `app/models/`, `app/repositories/`, `alembic/`
- **Mihir**: `app/integrations/`, intake/tracking API contracts, integration docs
- **Mehak + Ceren**: `.github/`, `Dockerfile`, `docker-compose.yml`, environment setup
- **Andy**: `tests/`, CI test checks, test data and validation rules
- **Shared implementation areas**: `app/services/`, `app/api/routes/`, `driver_ui/`

## Local run
```bash
cp .env.example .env
docker compose up --build
```

The root `.env` file is intentionally not committed; create it locally from `.env.example`.

Then open:
- API root: `http://localhost:8000/api/health`
- UI: `http://localhost:8000/`
- Docs: `http://localhost:8000/docs`

## Implementation rule
Keep business logic in `services/`, DB access in `repositories/`, external calls in `integrations/`, and HTTP handling in `api/routes/`.


## Connected React/Next driver portal
The separate driver portal under `frontend/driver-portal/` is now wired to the live backend APIs.

### Backend setup for the connected portal
```bash
cp .env.example .env
```

For local demo mode without an external Driver Service, enable the explicit fallback roster:
```bash
DRIVER_SERVICE_ENABLE_DEV_FALLBACK=true
```

Then start the backend:
```bash
docker compose up --build
```

### Frontend setup
```bash
cd frontend/driver-portal
cp .env.example .env.local
npm install
npm run dev
```

Frontend environment:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

The backend now allows requests from `http://localhost:3000` by default through `FRONTEND_ALLOWED_ORIGINS`.
