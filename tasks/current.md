# Current Status Snapshot

<!-- updated_at: 2026-07-09 -->
<!-- stale_after: 24h -->

> **Status**: Active implementation — production-cutover  
> **Updated At**: 2026-07-09  
> **Source Branch**: main  
> **Target Branch**: main  
> **Active Plan**: `plans/plan-20260709-production-cutover.md`

## Summary

- Docs aligned (prior commit).
- **In progress**: production cutover Phase 0–1 done; Phase 2 partial (auth/tasks/ai_settings postgres path); Phase 4.1–4.3 FE product gaps closed.
- Default runtime still `STORE_BACKEND=memory` (demo seed). Flip to `postgres` after `bash scripts/flyway-migrate.sh`.

## Done this slice

- Status machine + entity map docs; `pre_screen_common.status|db|security`
- Flyway: `app` + auth/exam/scoring/risk/judge V2 + resume V3
- `GatewayStoreRouter` + Auth/Task/AISettings repos
- FE: ResultDetail review/complete; ExamMonitor page; nav/router

## Exact next step

1. Start local Postgres + run `bash scripts/flyway-migrate.sh` and extend integration tests for auth/tasks.
2. Continue Phase 2.3–2.9: upload/candidate/paper/session/result/risk → Postgres.
3. Then Phase 3 demolish demo_store.

## Verification

- `uv run pytest tests/common tests/services/test_gateway_routes.py` — green
- `pnpm exec vitest run src/router/router.spec.ts` (apps/web) — green
- Flyway against live Postgres — deferred until stack is up
