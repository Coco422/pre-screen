# Pre-Screen

Pre-Screen is an MVP for technical candidate screening. This repository starts with the local
development foundation, shared backend settings, and the infrastructure stack needed for
PostgreSQL, Redis, MinIO, and Judge0.

## Local setup

1. Copy `.env.example` to `.env` and fill in any real credentials you need.
2. Install dependencies with `uv sync --group dev`.
3. Start the local stack with `bash scripts/dev-up.sh`.
4. Run tests with `uv run pytest`.

## Layout

- `packages/backend-common`: shared backend utilities and settings.
- `services`: FastAPI services for the MVP.
- `infra`: Dockerfiles and Nginx config for local infrastructure.
- `scripts`: helper scripts for local development.
