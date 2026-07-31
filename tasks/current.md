# Current Status Snapshot

> **Status**: Active cutover — durable screening loop landed  
> **Updated At**: 2026-07-31
> **Active Plan**: `plans/plan-20260709-production-cutover.md`

## Already done

| Slice | Status |
|-------|--------|
| Phase 0–1 schema/status/db | Done |
| 2.1 Auth | Done |
| 2.2 Tasks | Done |
| 2.3 Uploads + parse job + MinIO | Done |
| 2.4 Candidates | Done |
| 2.5 Papers generate/get/update/publish | Done (`ExamRepository`) |
| 2.6 Exam start/heartbeat/answer/submit | Done |
| 2.7 Coding submit persistence | Done (Judge0 still external) |
| 2.8 Results + review + complete-screening | Done |
| 2.9 Risk events + monitor list | Done |
| 2.10 AI settings | Done |
| Phase 4.1–4.3 FE product gaps | Done earlier |
| Frontend P0: build/test 恢复 + fail closed + 4.4 错误态（2026-07-31 代码完成，待手动联调验收） | Done |

## Still open

- Phase 3: remove `demo_store` / seed isolation  
- Frontend P0 手动验收（代码已完成，待真实流程联调；handoff: `tasks/notes/2026-07-19-frontend-p0-handoff.md`）
- Phase 5 workers / observability / runbooks  
- Deferred: notifications, avatar/password, WebSocket monitor  

## Runtime

```bash
bash scripts/flyway-migrate.sh   # or apply-sql-migrations.py
# STORE_BACKEND=postgres (compose default)
bash scripts/dev-up.sh
```

## Verification

- `tests/services/test_postgres_exam_loop.py` — durable paper→exam→review  
- `tests/services/test_postgres_candidate_store.py` — upload/candidate  
- Memory gateway routes still pass with forced `STORE_BACKEND=memory`  
