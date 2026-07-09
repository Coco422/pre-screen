# Pre-Screen

技术岗招聘智能初筛平台（本地部署）。HR 上传简历 → 多模态解析与画像 → AI 辅助出题 → 发卷 → 候选人在线考试（含 Judge0 代码题）→ 评分与风控。

## 当前阶段（2026-07-09）

| 维度 | 状态 |
|------|------|
| 产品主链路 | 可用（演示 / 内网联调） |
| 对外 API | Gateway `/api/admin/*` + `/api/public/*` 契约较完整 |
| 实现形态 | 默认 `STORE_BACKEND=memory`（demo_store seed）；可切 `postgres` 仓储路径 |
| 生产化 | Active plan：[`plans/plan-20260709-production-cutover.md`](plans/plan-20260709-production-cutover.md)（Phase 0–1 + 部分 2/4 已落地） |

权威文档：

- 产品：`docs/spec.md`
- 页面/接口：`docs/page-api/` + [`docs/page-api/AUDIT.md`](docs/page-api/AUDIT.md)
- 架构快照：`docs/architecture/snapshots/2026-07-09-mvp-demo-gateway.md`
- 任务快照：`tasks/current.md`

## Local setup

1. Copy `.env.example` to `.env` and fill credentials（AI key、Judge0 等）。
2. Python：`uv sync --group dev`
3. Web：`cd apps/web && pnpm install`（或沿用仓库锁文件工具）
4. 起依赖与网关：`bash scripts/dev-up.sh`
5. 迁移：`bash scripts/flyway-migrate.sh`（生产路径必需）
6. 可选：`.env` 设 `STORE_BACKEND=postgres` 启用 Auth/Tasks/AI settings 持久化路径
7. 测试：`uv run pytest`；前端在 `apps/web` 内按 package scripts

默认入口：

- Web：经 nginx 或 Vite dev（见 `scripts/dev-up.sh` / compose）
- Gateway：`http://localhost:8000`（`/healthz`）

## Judge0

macOS arm64 默认使用共享 Judge0 host（见 `.env.example` / compose 中 `JUDGE0_BASE_URL`），避免 Docker Desktop 对 isolate/cgroup 的限制。

若在 AMD Linux 上启用捆绑 Judge0：

```bash
COMPOSE_PROFILES=judge0-local docker compose up -d judge0-db judge0-redis judge0 judge0-workers judge0-init
```

## Layout

| 路径 | 说明 |
|------|------|
| `apps/web` | Vue 3 管理端 + 考试端 |
| `services/gateway` | 对外 BFF（当前含 demo_store） |
| `services/resume` | 简历解析领域与 API |
| `services/exam` | 模板/试卷/会话领域与 API |
| `services/judge_bridge` | Judge0 桥接 |
| `services/scoring` | 评分领域 |
| `services/risk` | 风控事件 |
| `packages/backend-common` | 配置、AI/Judge0 客户端、app factory |
| `database/flyway` | 分 schema 迁移（resume 较完整，其余待 production plan） |
| `docs/` | 规格、page-api、架构、研究 |
| `plans/` | 执行计划（含 production-cutover） |
| `tasks/` | current / todos / lessons |
| `scripts/` | dev-up、migrate、verify、烟测 |
| `infra/` | Dockerfiles、nginx、Judge0 |
| `deploy/` | runbooks / checklists（运维） |

## Development notes

- 前端调用统一走 Gateway；不要假设浏览器直连各微服务。
- 改接口时同步 `docs/page-api/` 与 `AUDIT.md`。
- 非琐碎改动前读 `AGENTS.md` / `CLAUDE.md` 与 active plan Task Breakdown。
