# Pre-Screen

Pre-Screen is an MVP for technical candidate screening. This repository starts with the local
development foundation, shared backend settings, and the local infrastructure needed for
PostgreSQL, Redis, and MinIO. Judge0 is developed against a dedicated AMD Linux host. The
application services and web app are added in later
tasks.

## Local setup

1. Copy `.env.example` to `.env` and fill in any real credentials you need.
2. Install dependencies with `uv sync --group dev`.
3. Start the local stack with `bash scripts/dev-up.sh`.
4. Run tests with `uv run pytest`.

## Judge0 note

macOS arm64 development uses the shared Judge0 host at `http://192.168.100.189:2360` by default.
This avoids Docker Desktop issues with `isolate` and cgroup support.

If you later need to boot the bundled local Judge0 stack on an AMD Linux host, enable the
`judge0-local` compose profile explicitly:

```bash
COMPOSE_PROFILES=judge0-local docker compose up -d judge0-db judge0-redis judge0 judge0-workers judge0-init
```

## Layout

- `packages/backend-common`: shared backend settings used by the bootstrap test.
- `infra`: Dockerfiles and Nginx config for the local development scaffolding.
- `scripts`: helper scripts for local development.
- `tests`: the Task 1 settings test.
