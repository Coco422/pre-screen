#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
cd "$repo_root"

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

wait_for_http() {
  local label="$1"
  local url="$2"
  local expected="$3"
  local deadline=$((SECONDS + 600))
  local body

  while (( SECONDS < deadline )); do
    if body="$(curl -fsS "$url" 2>/dev/null)"; then
      if [[ -z "$expected" || "$body" == *"$expected"* ]]; then
        printf 'ok: %s\n' "$label"
        return 0
      fi
    fi
    sleep 2
  done

  echo "timed out waiting for ${label} at ${url}" >&2
  return 1
}

wait_for_command() {
  local label="$1"
  shift
  local deadline=$((SECONDS + 600))

  while (( SECONDS < deadline )); do
    if "$@" >/dev/null 2>&1; then
      printf 'ok: %s\n' "$label"
      return 0
    fi
    sleep 2
  done

  echo "timed out waiting for ${label}" >&2
  return 1
}

retry() {
  local attempts="$1"
  shift
  local try=1

  until "$@"; do
    if (( try >= attempts )); then
      return 1
    fi
    echo "retry ${try}/${attempts} failed, trying again..." >&2
    try=$((try + 1))
    sleep 2
  done
}

compose config >/dev/null

judge0_base_url="${JUDGE0_BASE_URL:-http://192.168.100.189:2360}"

compose up -d --build --force-recreate --remove-orphans \
  postgres \
  redis \
  minio \
  minio-init \
  gateway \
  web \
  nginx

wait_for_command "postgres ready" compose exec -T postgres pg_isready -U postgres -d prescreen
wait_for_command "redis ready" compose exec -T redis redis-cli ping
wait_for_http "minio live probe" "http://localhost:9000/minio/health/live" ""
wait_for_http "remote judge0 languages" "${judge0_base_url}/languages" "["

JUDGE0_BASE_URL="$judge0_base_url" uv run python scripts/check_judge0.py

bash scripts/flyway-migrate.sh

uv run pytest -q
(cd apps/web && npm run test -- router.spec.ts examSession.spec.ts)
(cd apps/web && npm run build)

wait_for_http "gateway via nginx" "http://localhost/api/healthz" '"service":"gateway"'
wait_for_http "web via nginx" "http://localhost/" "<!doctype html>"

compose exec -T postgres pg_isready -U postgres -d prescreen
compose exec -T redis redis-cli ping | grep -qx PONG
compose logs --no-color minio-init | grep -Fq "minio bootstrap complete"

echo "local stack verification passed"
