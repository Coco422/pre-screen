# Current Status Snapshot

<!-- generated-by: manual alignment 2026-07-09 -->
<!-- updated_at: 2026-07-09 -->
<!-- stale_after: 24h -->

> **Status**: Planning / Ready for production-cutover execution  
> **Updated At**: 2026-07-09  
> **Source Branch**: main  
> **Target Branch**: main  
> **Stale After**: 24h  
> **Reason**: doc alignment + new active plan  
> **Derived From**: git HEAD, docs/page-api/AUDIT.md, plans/plan-20260709-production-cutover.md, handoff

## Summary

- MVP **产品主链路已通**（Gateway demo_store 编排 + 部分真实 domain）。
- 文档已与代码重新对齐（page-api AUDIT/README、FE plans 标 Done、README、架构 snapshot）。
- **Active plan**：`plans/plan-20260709-production-cutover.md`（去 demo → Postgres/仓储/异步/MinIO/薄 BFF）。
- Working tree may contain doc-only changes from this alignment session.

## Active Artifacts

| Artifact | Path |
|----------|------|
| Spec | `docs/spec.md` |
| Active plan | `plans/plan-20260709-production-cutover.md` |
| API audit | `docs/page-api/AUDIT.md` |
| Architecture snapshot | `docs/architecture/snapshots/2026-07-09-mvp-demo-gateway.md` |
| Deferred ledger | `tasks/todos.md` |
| Handoff | `.ai/harness/handoff/current.md` |

## Completed recently (code, pre-alignment)

- FE 文案/布局精简（plans 20260707 两份，Status=Done）
- AI settings 页 + Gateway AI/settings API
- Result review / complete-screening / monitor HTTP API（前端复核与监控页未接）
- 简历解析 pipeline、ExamShell、管理端主流程页面

## Exact next step

1. 人工确认 `plans/plan-20260709-production-cutover.md` 范围与切片顺序。  
2. 批准后从 **Phase 0（状态机冻结 + demo_store 映射）** 或 **Phase 4 产品补齐（结果复核 FE）** 开干。  
3. 执行期只更新 active plan 的 `## Task Breakdown` checkbox，不把执行清单复制进本文件。

## Known gaps (tracked in plan)

- demo_store 内存权威；重启丢业务数据  
- 多数 Flyway schema 空壳；服务 repo 内存 dict  
- 结果详情 FE 未接 review/complete-screening  
- `/admin/monitor` 无页面  
- WebSocket 监考 / 多租户等 → `tasks/todos.md`
