#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-course-app}"
SERVICE="${SERVICE:-app}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
MAX_TRIES="${MAX_TRIES:-20}"
SLEEP_SEC="${SLEEP_SEC:-2}"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

info() {
  echo "[INFO] $*"
}

resolve_cid() {
  local cid=""
  cid="$(docker ps --filter "name=^/${CONTAINER_NAME}$" --format '{{.ID}}' || true)"
  if [[ -z "${cid}" ]]; then
    cid="$(docker compose ps -q "${SERVICE}" 2>/dev/null || true)"
  fi
  echo -n "${cid}"
}

CID="$(resolve_cid)"
if [[ -z "${CID}" ]]; then
  die "Container not found. Make sure it's running (e.g. 'docker compose up -d')"
fi

STATE="$(docker inspect --format='{{.State.Status}}' "${CID}")"
if [[ "${STATE}" != "running" ]]; then
  die "Container state is '${STATE}', expected 'running'"
fi
info "Container '${CONTAINER_NAME}' is running (CID=${CID})"

UID_IN="$(docker exec "${CID}" id -u)"
if [[ "${UID_IN}" == "0" ]]; then
  die "Process inside container runs as root (uid=0)"
fi
info "Non-root OK: uid=${UID_IN}"

HEALTH_PRESENT="$(docker inspect --format='{{json .State.Health}}' "${CID}")"
if [[ -z "${HEALTH_PRESENT}" || "${HEALTH_PRESENT}" == "null" ]]; then
  die "No HEALTHCHECK defined in the image (.State.Health is empty)"
fi

STATUS=""
for i in $(seq 1 "${MAX_TRIES}"); do
  STATUS="$(docker inspect --format='{{.State.Health.Status}}' "${CID}")"
  if [[ "${STATUS}" == "healthy" ]]; then
    info "Healthcheck OK: status=healthy"
    break
  fi
  echo "Waiting for healthy... try ${i}/${MAX_TRIES} (current: ${STATUS:-unknown})"
  sleep "${SLEEP_SEC}"
done
[[ "${STATUS}" == "healthy" ]] || (docker logs "${CID}" || true; die "Container did not become healthy")

curl -fsS "${HEALTH_URL}" >/dev/null
info "HTTP probe OK: ${HEALTH_URL}"

if docker exec "${CID}" command -v curl >/dev/null 2>&1; then
  docker exec "${CID}" curl -fsS http://127.0.0.1:8000/health >/dev/null \
    && info "In-container HTTP probe OK: http://127.0.0.1:8000/health"
fi

echo "All checks passed ✅"
