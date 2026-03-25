# Farm2Fork Delivery Execution Service

Baseline backend + driver UI boilerplate for your team.

## Stack
- FastAPI backend
- PostgreSQL
- SQLAlchemy
- Alembic
- HTML/CSS/JavaScript driver UI
- Leaflet + OpenStreetMap for map rendering

## Features included
- `/api/health`
- sample deliveries, drivers, assignments endpoints
- driver dashboard page
- Leaflet map scaffold
- OpenStreetMap tiles
- clean frontend/backend separation

## Run locally
```bash
cp .env.example .env
docker-compose up --build
```

Then open:
- App: `http://localhost:8000/`
- Dashboard: `http://localhost:8000/dashboard`
- Health: `http://localhost:8000/api/health`

## Notes
The current repositories are in-memory placeholders so your team can start immediately.
Replace them with PostgreSQL-backed implementations as development proceeds.
