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

Then open:
- API root: `http://localhost:8000/api/health`
- UI: `http://localhost:8000/`
- Docs: `http://localhost:8000/docs`

## Implementation rule
Keep business logic in `services/`, DB access in `repositories/`, external calls in `integrations/`, and HTTP handling in `api/routes/`.


## React + TypeScript driver frontend
A separate React/TypeScript frontend has been added under `frontend/driver-portal/`.

Why this is a good fit:
- The backend remains Python/FastAPI and continues to own business logic, persistence, and integrations.
- The frontend can still consume all existing endpoints over HTTP.
- OpenStreetMap and Leaflet are frontend-friendly and can be added without changing the backend stack.
- PostgreSQL remains backend-only, which is the correct architecture.

Suggested local workflow:
```bash
# terminal 1
cp .env.example .env
docker compose up --build

# terminal 2
cd frontend/driver-portal
cp .env.example .env.local
npm install
npm run dev
```

Default URLs:
- Backend API: `http://localhost:8000`
- Backend docs: `http://localhost:8000/docs`
- React driver portal: `http://localhost:3000`
