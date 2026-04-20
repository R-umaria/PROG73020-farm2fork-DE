FROM python:3.11-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x docker/api-entrypoint.sh

EXPOSE 8000
CMD ["./docker/api-entrypoint.sh"]

FROM node:20-alpine AS frontend

WORKDIR /frontend

COPY frontend/driver-portal/package*.json ./
RUN npm ci

COPY frontend/driver-portal .

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
