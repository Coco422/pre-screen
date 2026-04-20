# Pre-Screen

Pre-Screen is an MVP for technical candidate screening. This repository starts with the local
development foundation, shared backend settings, and the local infrastructure needed for
PostgreSQL, Redis, MinIO, and Judge0. The application services and web app are added in later
tasks.

## Local setup

1. Copy `.env.example` to `.env` and fill in any real credentials you need.
2. Install dependencies with `uv sync --group dev`.
3. Start the local stack with `bash scripts/dev-up.sh`.
4. Run tests with `uv run pytest`.

## Layout

- `packages/backend-common`: shared backend settings used by the bootstrap test.
- `infra`: Dockerfiles and Nginx config for the local development scaffolding.
- `scripts`: helper scripts for local development.
- `tests`: the Task 1 settings test.
