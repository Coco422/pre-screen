#!/bin/sh
set -eu

echo "waiting for judge0 postgres to accept connections"
until pg_isready \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" >/dev/null 2>&1; do
  sleep 2
done

echo "waiting for judge0 language seeds"
until PGPASSWORD="$POSTGRES_PASSWORD" psql \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  -Atqc "select count(*) from languages" | grep -Eq '^[1-9][0-9]*$'; do
  sleep 2
done

echo "reconciling judge0 language customizations"
stable_checks=0
while [ "$stable_checks" -lt 5 ]; do
  current_run_cmd="$(
    PGPASSWORD="$POSTGRES_PASSWORD" psql \
      -h "$POSTGRES_HOST" \
      -p "$POSTGRES_PORT" \
      -U "$POSTGRES_USER" \
      -d "$POSTGRES_DB" \
      -Atqc "select run_cmd from languages where id = 62"
  )"

  if echo "$current_run_cmd" | grep -Fq "MaxMetaspaceSize=256m"; then
    stable_checks=$((stable_checks + 1))
    sleep 2
    continue
  fi

  stable_checks=0
  PGPASSWORD="$POSTGRES_PASSWORD" psql \
    -h "$POSTGRES_HOST" \
    -p "$POSTGRES_PORT" \
    -U "$POSTGRES_USER" \
    -d "$POSTGRES_DB" \
    -f /bootstrap/customize-languages.sql >/dev/null
  sleep 2
done

echo "judge0 bootstrap complete"
