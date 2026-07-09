# Architecture Snapshot: MVP Demo Gateway

> **Date**: 2026-07-09  
> **Status**: Current as-of snapshot（非目标态）  
> **Supersede plan**: `plans/plan-20260709-production-cutover.md`

## Summary

Pre-Screen MVP 对外呈现完整 HR + 考生闭环，但**运行时状态权威**集中在 Gateway 进程内的 `GatewayDemoStore`。领域服务代码存在且部分被进程内复用，**尚未形成「服务 API + Postgres 仓储」的生产边界**。

## Runtime topology (local)

```
Browser
  → nginx(:80) / vite proxy
    → web (static)
    → gateway(:8000)  ← demo_store (memory)
         ├─ import resume.parse_resume_file
         ├─ import resume_intelligence (AI)
         ├─ import exam.paper_generator
         ├─ import scoring.domain
         └─ HTTP → Judge0 (external host)

postgres / redis / minio  ← 已部署，主路径几乎未用为业务权威
```

Compose 默认服务：`postgres`, `redis`, `minio`, `gateway`, `web`, `nginx`。  
Judge0 默认外置；`judge0-local` profile 可选。

## Ownership today

| 能力 | 代码位置 | 状态权威 |
|------|----------|----------|
| Admin / Public API | gateway `admin.py` / `public_exam.py` | demo_store |
| 简历解析算法 | resume `parsing/*`, `tasks/parse_resume.py` | 调用方内存 / 临时目录 |
| 出题 | exam `paper_generator.py` | demo_store papers |
| 评分 | scoring `domain/*` | demo_store results |
| 风控 | risk repo + gateway 记录 | 内存 |
| 判题 | judge_bridge + Judge0 | 外部 Judge0 + store 提交缓存 |

## Schema readiness

| Schema | Flyway | 使用情况 |
|--------|--------|----------|
| resume | V1+V2 有表 | 代码 repo 仍内存；表未成主路径 |
| exam / auth / scoring / risk / judge | 空/bootstrap | 未承载业务 |

## Target delta (one slide)

| 现在 | 目标（cutover plan） |
|------|----------------------|
| demo_store 字典 | Postgres 表 + repository |
| 进程内 import 编排 | 薄 BFF + application service；可演进 HTTP |
| 同步解析线程 | Redis worker 异步 job |
| 本地 temp PDF | MinIO object key 权威 |
| 重启丢数据 | 重启可恢复 |
| 结果复核仅后端 | FE 接线 + 落库 |

## Related docs

- Product: `docs/spec.md`
- API audit: `docs/page-api/AUDIT.md`
- Design intent: `docs/superpowers/specs/2026-04-21-pre-screen-design.md`
- Active plan: `plans/plan-20260709-production-cutover.md`
