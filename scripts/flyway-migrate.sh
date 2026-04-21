#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"

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

for service in auth resume exam judge scoring risk; do
  if [[ -n "$docker_network_mode" ]]; then
    docker run --rm \
      --network "$docker_network_mode" \
      -v "$repo_root/database/flyway:/flyway/conf" \
      -w /flyway/conf \
      flyway/flyway:11 \
      -url="jdbc:postgresql://${db_host}:5432/prescreen" \
      -configFiles="/flyway/conf/${service}/flyway.conf" migrate
  else
    docker run --rm \
      -v "$repo_root/database/flyway:/flyway/conf" \
      -w /flyway/conf \
      flyway/flyway:11 \
      -url="jdbc:postgresql://${db_host}:5432/prescreen" \
      -configFiles="/flyway/conf/${service}/flyway.conf" migrate
  fi
done
