#!/usr/bin/env bash
set -euo pipefail

COMPOSE_PROFILES="${COMPOSE_PROFILES:-dev}"
SERVICE="${SERVICE:-app}"
CONTAINER_NAME="${CONTAINER_NAME:-course-app}"

echo "[1/3] Building images (profile: ${COMPOSE_PROFILES})..."
docker compose --profile "${COMPOSE_PROFILES}" build "${SERVICE}"

echo "[2/3] Starting containers..."
docker compose --profile "${COMPOSE_PROFILES}" up -d "${SERVICE}"

echo "[3/3] Status:"
docker compose ps

echo
echo "Logs (press Ctrl+C to stop following, containers keep running):"
docker compose logs -f "${SERVICE}"
