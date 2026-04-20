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

## Judge0 note

The local Judge0 stack follows the official split deployment pattern: one API container, one
worker container, a dedicated Postgres database, and a dedicated Redis instance with password
protection.

If you are running on macOS with Docker Desktop, Judge0 may still fail to execute code even when
the API is healthy. Judge0 uses `isolate`, which expects Linux cgroup features that are not always
available through Docker Desktop's VM layer. If you see errors mentioning `/sys/fs/cgroup/...` or
`/box/...`, move the Judge0 runtime to a Linux host or VM and keep the rest of the stack local.

## Layout

- `packages/backend-common`: shared backend settings used by the bootstrap test.
- `infra`: Dockerfiles and Nginx config for the local development scaffolding.
- `scripts`: helper scripts for local development.
- `tests`: the Task 1 settings test.
