#!/usr/bin/env bash
set -euo pipefail

for service in auth resume exam judge scoring risk; do
  docker run --rm \
    -v "$PWD/database/flyway:/flyway/conf" \
    -w /flyway/conf \
    flyway/flyway:11 \
    -configFiles="/flyway/conf/${service}/flyway.conf" migrate
done
