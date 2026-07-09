#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

# Prefer host-side apply when Docker cannot mount the repo volume (e.g. /Volumes paths).
if [[ "${FLYWAY_FORCE_DOCKER:-0}" != "1" ]]; then
  if command -v uv >/dev/null 2>&1; then
    echo "applying SQL migrations via host psycopg (scripts/apply-sql-migrations.py)"
    cd "$repo_root"
    uv run python scripts/apply-sql-migrations.py
    exit 0
  fi
fi

docker_network_mode="${FLYWAY_DOCKER_NETWORK_MODE:-}"

if [[ -z "$docker_network_mode" ]]; then
  case "$(uname -s)" in
    Linux)
      docker_network_mode="host"
      ;;
  esac
fi

if [[ "$docker_network_mode" == "host" ]]; then
  db_host="${FLYWAY_DB_HOST:-localhost}"
else
  db_host="${FLYWAY_DB_HOST:-host.docker.internal}"
fi

for service in app auth resume exam judge scoring risk; do
  if [[ -n "$docker_network_mode" ]]; then
    docker run --rm \
      --network "$docker_network_mode" \
      -v "$repo_root/database/flyway:/flyway/conf" \
      -w /flyway/conf \
      flyway/flyway:11 \
      -url="jdbc:postgresql://${db_host}:5432/prescreen" \
      -user=postgres \
      -password=postgres \
      -configFiles="/flyway/conf/${service}/flyway.conf" migrate
  else
    docker run --rm \
      -v "$repo_root/database/flyway:/flyway/conf" \
      -w /flyway/conf \
      flyway/flyway:11 \
      -url="jdbc:postgresql://${db_host}:5432/prescreen" \
      -user=postgres \
      -password=postgres \
      -configFiles="/flyway/conf/${service}/flyway.conf" migrate
  fi
done
