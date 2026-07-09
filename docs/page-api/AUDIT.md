# Pre-Screen 接口对齐审计

> 审计时间：2026-07-09（相对 2026-07-07 版本刷新）
> 对比来源：`docs/page-api/*.md` vs `services/gateway/app/api/admin.py` + `public_exam.py` + `demo_store.py` + `apps/web`

## 总体结论

| 维度 | 状态 |
|------|------|
| Gateway 主链路 HTTP 契约 | **已齐**：管理端 + 考生端闭环可用 |
| 前端主流程接线 | **基本齐**：结果复核/归档、考试监控页仍缺接线 |
| 持久化 / 服务边界 | **仍是 demo 形态**：Gateway 内存 `demo_store` 编排；各服务 repo 多为内存 dict |
| 与生产形态差距 | 见 active plan：`plans/plan-20260709-production-cutover.md` |

**主链路接口齐全，可演示、可联调；不可当作生产多实例/可恢复系统。**

---

## 已有且可用（Gateway HTTP）

| 文档页面 | 接口 | 后端 | 前端接线 |
|----------|------|------|----------|
| 01-login | `POST /admin/session/login` | ✅ demo_store | ✅ |
| 01-login | `GET /admin/session/me` | ✅ | ✅ |
| 02-dashboard | `GET /admin/dashboard` | ✅ | ✅ |
| 03-task-list | `GET /admin/tasks` | ✅ | ✅ |
| 04-task-create | `POST /admin/tasks` | ✅ | ✅ |
| 05-task-detail | `GET /admin/tasks/:taskId` | ✅ | ✅ |
| 05-task-detail | `POST /admin/tasks/:taskId/uploads` | ✅（解析走 resume 领域函数） | ✅ |
| 05-task-detail | `GET /admin/uploads/:uploadId` | ✅ | ✅ |
| 06-candidate-list | `GET /admin/candidates` | ✅（多筛选参数） | ✅ |
| 07-candidate-detail | `GET /admin/candidates/:id` | ✅ | ✅ |
| 07-candidate-detail | `GET /admin/candidates/:id/resume.pdf` | ✅ | ✅ |
| 08-candidate-edit | `PUT /admin/candidates/:id` | ✅ | ✅ |
| 09-paper-editor | `POST /admin/candidates/:id/papers/generate` | ✅ | ✅ |
| 09-paper-editor | `GET /admin/papers/:paperId` | ✅ | ✅ |
| 09-paper-editor | `PUT /admin/papers/:paperId` | ✅ | ✅ |
| 09-paper-editor | `POST /admin/papers/:paperId/publish` | ✅ | ✅ |
| 10-result-list | `GET /admin/results` | ✅ | ✅ |
| 11-result-detail | `GET /admin/results/:resultId` | ✅ | ✅ 查看 |
| 11-result-detail | `PUT /admin/results/:id/review` | ✅（2026-07-08） | ❌ 未接 |
| 11-result-detail | `POST /admin/results/:id/complete-screening` | ✅（2026-07-08） | ❌ 未接 |
| 12/13/14 exam | public exams 全套 | ✅ | ✅ ExamShell |
| 15-ai-settings | `GET/PUT /admin/settings/ai` + `POST .../test` | ✅ | ✅ `/admin/settings` |
| 16-monitor | `GET /admin/monitor/sessions` | ✅ HTTP 轮询级 | ❌ 无页面 |
| 16-monitor | `POST /admin/monitor/sessions/:id/force-submit` | ✅ | ❌ 无页面 |

### 考生端 public 明细

| 接口 | 状态 |
|------|------|
| `GET /public/exams/:token` | ✅ |
| `POST /public/exams/:token/start` | ✅ |
| `PUT /public/exams/:token/answers/:qId` | ✅ |
| `POST /public/exams/:token/heartbeat` | ✅ |
| `POST /public/exams/:token/risk-events` | ✅ |
| `POST /public/exams/:token/coding/run` | ✅ |
| `POST /public/exams/:token/coding/submit` | ✅ |
| `POST /public/exams/:token/submit` | ✅ |

---

## 仍缺或仅部分实现

| 文档页面 | 接口 / 能力 | 状态 | 优先级 |
|----------|-------------|------|--------|
| 09-paper-editor | `POST /admin/papers/:id/regenerate-llm-questions` | 未实现 | P2 |
| 11-result-detail | 前端修分 / 归档 UI | 后端有，前端无 | P1 |
| 16-monitor | `/admin/monitor` 页面 | 后端有 HTTP，无路由/页 | P1 |
| 16-monitor | WebSocket 双向通道 | 仅设计，无实现 | P2（生产化后置） |
| 07-candidate-detail | `self_description` / `awards` 独立字段 | 画像结构基本够，字段未拆 | P2 |
| 路由 | `/admin/papers` 列表、`/admin/risk` | Placeholder | P3 |

---

## 实现形态说明（审计时必须读）

当前 Gateway **不是**「薄 BFF + 各服务 HTTP + Postgres」：

1. `services/gateway/app/domain/demo_store.py`（约 2k 行）是**运行时状态权威**（内存 + 锁）。
2. 领域能力以**进程内 import** 方式复用：
   - `services.resume.app.tasks.parse_resume.parse_resume_file`
   - `services.gateway.app.domain.resume_intelligence`
   - `services.exam.app.domain.paper_generator`
   - `services.scoring.app.domain.*`
3. 各服务自带 repo 仍多为**内存 dict**（resume / exam / risk）。
4. Flyway：仅 `resume` schema 有实质表（candidates / files / parse pipeline）；`exam` / `auth` / `scoring` / `risk` / `judge` 多为空 schema bootstrap。
5. Compose 当前起 **gateway + web + nginx + postgres/redis/minio**；未默认起 resume/exam 等独立服务进程。

因此：接口「已有」= **契约与行为在 demo 路径下可用**，不等于生产持久化完成。

---

## 状态机（文档建议 vs 当前）

| 业务阶段 | 建议状态 | 当前常见状态 | 备注 |
|----------|----------|--------------|------|
| PDF 上传 | 已上传简历 | 解析中 | 细粒度未拆 |
| 解析 / 画像 | 信息提取中 / 信息整理中 | 解析中 / 待审核 | demo 粗粒度 |
| 出卷 | 拟出卷中 → 待发卷 | 待发卷 | |
| 发卷 | 已发卷 | 待开考 | 文案不一致 |
| 考试中 | 进行中考试 | 已开考 | |
| 交卷 | 已交卷 | 已完成 / 已交卷混用 | complete-screening 已后端支持归档 |
| 复核 | 评分复核中 | review_status 字段有 | 前端未驱动 |
| 完成 | 已完成筛选 / 已归档 | complete-screening 可写 | 前端未驱动 |

统一状态枚举应在 production-cutover plan 中一次性冻结。

---

## 建议下一步（文档层）

1. **Active plan**：`plans/plan-20260709-production-cutover.md`（去 demo、靠拢生产）。
2. **产品补齐（可与生产化并行）**：结果详情 FE 接线 + 监控页（HTTP 轮询即可）。
3. **文档维护**：本 AUDIT 与 `docs/page-api/README.md` 以「契约 + 实现形态」双栏为准；避免只写「有接口」误导为「已生产」。
