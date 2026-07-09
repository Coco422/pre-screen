# Current Status Snapshot

> **Status**: Active — production cutover  
> **Updated At**: 2026-07-09  
> **Active Plan**: `plans/plan-20260709-production-cutover.md`

## Latest

Durable **tasks / uploads / candidates / AI settings / auth** on Postgres + MinIO when `STORE_BACKEND=postgres` (compose default).

Restarting gateway via `dev-up` no longer wipes uploaded resumes (MinIO volume + DB).

Still memory/demo for: papers generate/publish, exam session, scoring results, monitor (Phase 2.5–2.9).

## How to run durable mode

```bash
bash scripts/flyway-migrate.sh   # or uv run python scripts/apply-sql-migrations.py
bash scripts/dev-up.sh           # STORE_BACKEND=postgres by default
```

## Next

- Phase 2.5–2.9：papers / sessions / results / risk 落库  
- Phase 3：拆除 demo_store  
