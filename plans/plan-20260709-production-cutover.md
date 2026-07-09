# Plan: 去 Demo → 生产形态 Cutover

> **Status**: Active
> **Created**: 2026-07-09
> **Slug**: production-cutover
> **Artifact Level**: work-package / multi-sprint
> **Promotion Reason**: MVP 主链路可演示，但状态权威在内存 demo_store；不可多实例、不可重启恢复、服务边界名存实亡
> **Verification Boundary**: Flyway migrate 全 schema 成功 + 重启后业务数据仍在 + 主链路 e2e（上传→出题→发卷→作答→交卷→复核）不依赖 seed 内存 + Gateway 无运行时读写 `demo_store` 业务实体
> **Rollback Surface**: feature flag / 双写窗口回切 demo_store；按切片 git revert；DB migration down 脚本仅限未上线表
> **Spec**: `docs/spec.md`
> **Contract / API truth**: `docs/page-api/` + `docs/page-api/AUDIT.md`
> **Architecture intent**: `docs/superpowers/specs/2026-04-21-pre-screen-design.md` §4

---

## 1. 决策摘要（P1 / P2 / P3）

### P1 — 真实系统边界（现状）

| 组件 | 现实角色 |
|------|----------|
| `apps/web` | 真实 UI；部分写操作未接（结果复核、监控） |
| `services/gateway` | **唯一对外 HTTP**；`demo_store` 是状态权威 |
| `services/resume|exam|scoring|risk|judge_bridge` | 有 API / domain，但 **repo 多为内存**；Gateway 常 **进程内 import domain**，不走服务 HTTP |
| Postgres | Compose 已起；**仅 resume 有实质表**；exam/auth/scoring/risk/judge 空 schema |
| Redis / MinIO | 基建在；异步任务与对象存储未成为主路径权威 |
| Judge0 | 外置 host；coding run/submit 已通 |

### P2 — 一条具体数据路径（当前 vs 目标）

**当前：上传简历**

```
Web POST /api/admin/tasks/:id/uploads
  → gateway.admin.create_uploads
  → demo_store 内存登记 upload
  → 线程/同步调用 parse_resume_file (resume 领域)
  → enrich_resume_profile (gateway resume_intelligence)
  → 写回 demo_store.candidates
```

**目标：上传简历**

```
Web POST /api/admin/tasks/:id/uploads
  → gateway BFF 鉴权 + 聚合
  → resume service: 写 MinIO + resume.resume_files (pending)
  → Celery/RQ worker: parse + multimodal + profile
  → 更新 parse_runs / candidates（Postgres）
  → gateway GET 只读聚合 DB/服务 API
```

### P3 — 设计不变量（必须守住）

1. **对外 API 路径与 page-api 契约尽量不变**（strangler；前端少改）。
2. **状态权威唯一**：每个实体只属于一个 schema/服务；Gateway 不长期持有业务真相。
3. **失败封闭**：解析/AI/判题失败要可观察状态，不静默假成功。
4. **本地数据不出域**：AI / 存储 / DB 仍本地部署约束。
5. **可重启**：进程重启后任务、候选人、试卷、会话、答卷、结果仍在。

---

## 2. 推荐架构策略

**Strangler + 仓储先行，服务进程后置。**

| 选项 | 做法 | 取舍 |
|------|------|------|
| A. 立刻微服务 HTTP 全拆 | Gateway 只转发，六服务独立进程 | 编排成本高，当前 domain 耦合紧，易双写逻辑 |
| **B. 推荐：Postgres 仓储 + Gateway 编排变薄** | 先把 repo 落库；Gateway 调 domain/service 模块或内部 client；compose 可后补独立进程 | 最快去掉 demo；边界清晰可演进 |
| C. 模块化单体 | 合并服务目录 | 与既有 mono-service 布局冲突，推倒成本大 |

**选定 B**，分三层推进：

1. **Data plane**：Flyway 表 + SQLAlchemy/psycopg 仓储替换内存 dict  
2. **Control plane**：拆 `demo_store` 为 application services（task/candidate/paper/session/result），无内存全局单例真相  
3. **Runtime plane**：Celery worker、MinIO 强制路径、可选独立服务进程与 health

---

## 3. Scope / Non-scope

### In scope（本 plan）

- 冻结候选人/任务/试卷/会话/结果 **状态枚举**
- 补齐 Flyway：`auth` / `exam` / `scoring` / `risk` /（按需）`gateway` 或 app 配置表
- 仓储落库：tasks、candidates、uploads、papers、invitations、sessions、answers、results、risk_events、admin sessions
- 简历 PDF：**MinIO** 为权威，本地 temp 仅处理缓存
- 解析/出题：**异步任务**（Redis broker）+ 可查询 job 状态
- Gateway 删除业务实体对 `demo_store` 的依赖（可保留 `fixtures/` 仅测用 seed）
- 鉴权：密码哈希 + session/token 表（仍可单租户）
- AI 配置持久化
- 产品缺口补齐：结果复核 FE、监控页（HTTP 轮询）、force-submit
- 重启恢复 e2e + 迁移脚本进 `verify-local-stack`

### Out of scope（明确不做）

- 多租户 / org 计费 / SSO
- WebSocket 监考升级、摄像头、设备指纹、请求 HMAC（记入 deferred）
- 题库运营后台完整产品化
- 自定义 Judge0 镜像
- 大规模水平扩展与分库
- 完美替换一切 seed 演示数据（允许 **显式 seed 命令** 灌库，但不进运行时权威）

---

## 4. 切片与 Task Breakdown

### Phase 0 — 契约与基线（0.5–1d）

- [x] 0.1 冻结状态枚举文档：写入 `docs/architecture/domains/status-machine.md` + `pre_screen_common.status`
- [x] 0.2 列出 `demo_store` 实体 → 目标表映射表（`docs/architecture/domains/entity-map.md`）
- [x] 0.3 基线测试清单：`tests/common` + gateway routes + web router vitest 已绿
- [x] 0.4 实现形态写入 AUDIT + architecture snapshot（文档 commit）

**Exit**：映射表评审通过；主链路测试基线绿色。

### Phase 1 — 数据面：Schema + 公共 DB 访问（2–3d）

- [x] 1.1 `packages/backend-common`：DB engine/session 工厂（`pre_screen_common.db`）
- [x] 1.2 Flyway `auth`：users / sessions（V2）
- [x] 1.3 Flyway `exam`：templates、papers、invitations、sessions、answer_drafts（V2）
- [x] 1.4 Flyway `scoring`：results（jsonb 含 reviews/notes）（V2）
- [x] 1.5 Flyway `risk`：events（V2）
- [x] 1.6 Flyway 扩展 `resume`：task 关联、profile/upload_jobs（V3）
- [x] 1.7 `app` schema：screening_tasks、ai_settings、id_counters
- [x] 1.8 `scripts/flyway-migrate.sh` 含 app；`verify-local-stack.sh` 尝试 migrate

**Exit**：空库 migrate 成功；表可手工插入/查询。（需本机 Postgres 运行后验证）

### Phase 2 — 仓储替换（按依赖序，4–6d）

原则：**接口行为不变，替换存储**；每个子切片可单独合并。  
开关：`STORE_BACKEND=memory|postgres`（默认 memory 保留 demo seed）。

- [x] 2.1 **Auth**：login / me → DB；bootstrap admin（env）；`GatewayStoreRouter` 路由
- [x] 2.2 **Tasks**：create/list/get task → Postgres repo
- [x] 2.3 **Resume parse job**：upload 元数据 + 异步 parse 写 `upload_jobs` / candidate profile（线程内，非 Celery）
- [x] 2.4 **Candidates**：list/detail/update 读 DB；PDF 存 MinIO 并流式返回
- [ ] 2.5 **Papers**：generate/update/get/publish + invitation token/code_hash 落库
- [ ] 2.6 **Exam session**：start、heartbeat、save_answer、submit 落库
- [ ] 2.7 **Coding**：run/submit 仍调 Judge0；submission 结果落库
- [ ] 2.8 **Scoring results**：submit 后写 result；review / complete-screening 落库
- [ ] 2.9 **Risk**：events 落库；monitor list 读 DB
- [x] 2.10 **AI settings**：Postgres repo + router 切换

**Exit**：Gateway 路径仍通；`demo_store` 业务字典可标记 deprecated；**杀 gateway 进程再启，数据仍在**。

### Phase 3 — 拆除 demo_store（1–2d）

- [ ] 3.1 将编排逻辑迁到 `services/gateway/app/application/*` 或对应 service 模块
- [ ] 3.2 删除/隔离 seed 到 `scripts/seed_demo.py`（显式执行）
- [ ] 3.3 禁止生产路径 `OBJECTIVE_DETAILS` 等硬编码题库作为唯一来源：迁到 exam 题库表或模板 JSON
- [ ] 3.4 CI/测试用 fixture DB 或 transaction rollback，不用全局内存单例

**Exit**：代码检索 `gateway_demo_store` 仅测试或删除；grep 主路径为零。

### Phase 4 — 产品闭环补齐（可与 Phase 2 并行，1–2d）

- [x] 4.1 前端 `ResultDetailView`：接 `PUT .../review` + `POST .../complete-screening`
- [x] 4.2 前端监控页 `/admin/monitor`：轮询 `GET .../monitor/sessions` + force-submit
- [x] 4.3 导航与权限：monitor 入口接真页；settings 已有
- [ ] 4.4 错误态：解析失败、AI 不可用、Judge0 超时 — 页面可见、可重试

**Exit**：HR 不打开后端日志也能完成「修分 → 通过/淘汰」与「查看在考会话」。

### Phase 5 — 运行形态靠拢生产（2–3d）

- [ ] 5.1 Compose：worker 服务（解析/评分任务）；健康检查
- [ ] 5.2 可选：独立起 `resume`/`exam` 进程，Gateway 改 HTTP client（若 Phase 2 模块边界已清）
- [ ] 5.3 结构化日志 + request_id 贯穿 upload→parse→publish
- [ ] 5.4 备份/恢复 runbook 草稿（`deploy/runbooks/`）
- [x] 5.5 README / verify-local-stack 部分对齐（migrate 钩子 + STORE_BACKEND env）
- [x] 5.6 架构 snapshot 写入 `docs/architecture/snapshots/`

**Exit**：文档描述的本地生产样形态可一键拉起；新人按 README 跑通主链路。

---

## 5. 测试策略

| 层级 | 内容 |
|------|------|
| 单元 | 状态机、评分、paper_generator、parse pipeline（已有延续） |
| 仓储集成 | pytest + 真实 Postgres（compose 或 testcontainers）；migrate 后 CRUD |
| API | Gateway 路由契约测试：与 page-api 路径对齐 |
| 重启测试 | 写实体 → restart gateway → GET 仍在 |
| E2E | 扩展 `tests/e2e`：admin 登录→任务→上传 fixture PDF→等待 parse→出卷→publish→exam submit→review |
| 前端 | vitest 覆盖 ResultDetail / Monitor 新接线 |

**不做**：用「前端 localStorage fallback」掩盖后端未落库。

---

## 6. Rollback / 失败处理

| 风险 | 处理 |
|------|------|
| 某切片落库后回归 | 该切片 feature flag `STORE_BACKEND=memory|postgres`（过渡期），默认 postgres |
| Migration 失败 | Flyway 按 schema 独立；坏迁移修 forward，不 rewrite 已发布版本号 |
| 双写不一致 | 过渡期只允许 **单写**（postgres）；memory 仅 fallback 读禁止 |
| AI/Judge0 外部依赖 | 失败写明确 job/result 错误态；不回滚已落库上传 |
| 大爆改前端 | API 契约冻结；FE 仅 Phase 4 增量 |

---

## 7. 最脆弱假设

1. **现有 domain 函数可在无 demo_store 上下文中纯函数式调用**（不依赖全局可变 seed）。  
   - 缓解：Phase 2 每个切片先抽纯输入/输出测试再换仓储。
2. **单库多 schema 足够**，短期内不需要服务间事件总线。  
   - 若异步与一致性复杂化，再引入 outbox；本 plan 不预埋。
3. **HR 单租户、弱密码策略可接受**。  
   - 若要对公网，需另开安全 hardening plan。

---

## 8. 建议执行顺序（给实施者）

```
Phase 0 → Phase 1 → (Phase 2.1–2.4) → Phase 4.1 并行
                 → (Phase 2.5–2.9) → Phase 4.2
                 → Phase 3 → Phase 5
```

优先垂直切片：**Task/Upload/Candidate 持久化** 价值最高（简历与画像是核心资产）。

---

## 9. 附录 A — 实体映射（初稿）

| demo_store 概念 | 目标 schema.table | 备注 |
|-----------------|-------------------|------|
| admin users / tokens | auth.users, auth.sessions | |
| tasks | app.screening_tasks 或 resume.tasks | 与候选人关联 |
| uploads / parse jobs | resume.resume_files, resume_parse_runs | 已有表可扩展 |
| candidates / profile | resume.candidates + profile jsonb | |
| papers / questions | exam.papers, exam.paper_questions | questions 可 jsonb |
| invitations | exam.invitations | token + code_hash |
| sessions / answers | exam.sessions, exam.answer_drafts | |
| coding submissions | judge.submissions 或 exam.coding_submissions | |
| results / reviews | scoring.results, scoring.question_reviews | |
| risk events | risk.events | |
| ai settings | app.ai_settings | |
| monitor view | 读 exam.sessions + risk 聚合 | 非独立真相 |

---

## 10. 附录 B — 与已完成工作的关系

| 已完成 | 本 plan 态度 |
|--------|----------------|
| page-api 主链路 26+ 接口 | **冻结为外部契约** |
| resume 解析 / AI enrich / paper_generator / scoring domain | **保留为领域实现**，换调用上下文 |
| FE 文案清理、ExamShell、AI settings 页 | 保留；Phase 4 只补复核与监控 |
| demo_store 内业务规则 | **迁移后删除**，不是长期 core |

---

## Promotion Gate

- **Merge unit**：按 Phase/子切片 PR，禁止「一周巨大 bang」
- **Done 定义**：Verification Boundary 全满足 + AUDIT 实现形态改为「Postgres 权威」+ README 可复现
- **下一步 plan（deferred）**：WebSocket 监考、多租户、题库运营、公网安全 hardening
