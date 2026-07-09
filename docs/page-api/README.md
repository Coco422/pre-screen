# Pre-Screen 页面接口总览

这组文档按页面拆分，面向前端与 Gateway 统一入口整理。

- 接口入口统一以 Gateway 为准：前端调用 `/api/admin/*` 和 `/api/public/*`。
- 状态标记约定：
  - `已有`：Gateway 已实现且主路径可调用
  - `建议扩展`：同名接口已有，字段/筛选/状态机仍不足
  - `建议新增`：仓库尚无该接口
  - `前端未接`：后端已有，页面未接线
- **权威对齐快照**：见 [AUDIT.md](./AUDIT.md)（2026-07-09 刷新）
- **生产化计划**：见 `plans/plan-20260709-production-cutover.md`

## 页面清单

- [01. 登录页](./01-login.md)
- [02. HR 工作台](./02-dashboard.md)
- [03. 任务中心](./03-task-list.md)
- [04. 新建筛选任务页](./04-task-create.md)
- [05. 任务详情与上传简历页](./05-task-detail.md)
- [06. 候选人列表页](./06-candidate-list.md)
- [07. 候选人详情页](./07-candidate-detail.md)
- [08. 编辑画像页](./08-candidate-edit.md)
- [09. 考卷编辑与发布页](./09-paper-editor-publish.md)
- [10. 结果中心列表页](./10-result-list.md)
- [11. 结果详情与评分复核页](./11-result-detail-review.md)
- [12. 考试身份验证页](./12-exam-verify.md)
- [13. 在线作答页](./13-exam-session.md)
- [14. 交卷完成页](./14-exam-submitted.md)
- [15. AI 配置管理](./15-ai-settings.md)
- [16. 考试实时监控与防作弊](./16-exam-monitor-anti-cheat.md)
- [17. 前端排版重设计需求](./17-frontend-layout-redesign.md)
- [18. 系统设置 / 账号 / 通知](./18-system-settings-and-account.md)
- [19. 考卷列表 + 异步生成考卷](./19-paper-list-and-generate-job.md)
- [接口对齐审计](./AUDIT.md)

## 路由对照（spec / 实现）

| 产品路由（目标） | 当前前端 | 备注 |
|------------------|----------|------|
| `/login` | ✅ | |
| `/admin/dashboard` | ✅ | |
| `/admin/tasks` / `new` / `:id` | ✅ | |
| `/admin/candidates` / `:id` / `edit` | ✅ | |
| `/admin/papers/:id` | ✅ 编辑器 | `/admin/papers` 列表仍为 Placeholder |
| `/admin/results` / `:id` | ✅ | 复核动作未接后端 |
| `/admin/settings` | ✅ AI 配置 | 文档曾写 `/admin/settings/ai`，实现为 `/admin/settings` |
| `/admin/monitor` | ❌ | 后端 monitor API 有，无页 |
| `/exam/:token` | ✅ ExamShell | start/session/submitted 子路径 redirect 到 shell |

## 候选人主状态建议

真实业务比 demo 粗状态更细，生产化时应前后端统一：

| 业务阶段 | 建议状态 | 当前常见状态 |
| --- | --- | --- |
| PDF 刚上传 | `已上传简历` | `解析中` |
| PyMuPDF + 多模态提取 | `信息提取中` | `解析中` |
| LLM 信息整理与核验 | `信息整理中` | `待审核` / `解析中` |
| 生成候选人专属题目 | `拟出卷中` | 无单独状态 |
| 题目草稿已保存 | `待发卷` | `待发卷` |
| 已生成考试链接和验证码 | `已发卷` | `待开考` |
| 候选人已进入考试 | `进行中考试` | `已开考` |
| 候选人已提交 | `已交卷` | `已完成` / `已交卷` |
| HR 正在修分复核 | `评分复核中` | `review_status` 后端有 |
| HR 确认通过筛选 | `已完成筛选` | complete-screening 后端有 |
| 最终进入人才档案 | `已归档` | complete-screening 可写 |

## 当前代码与目标的差异（2026-07-09）

### 已对齐（相对早期 page-api 描述）

- 已有独立 `GET /admin/dashboard`，前端工作台不再只能本地拼三个列表。
- 候选人列表筛选已扩展：`status` / `role` / `keyword` / `task_id` / `pending_review` / `paper_sent` / `paper_status` / `risk_level` / `sort_by` / `order`。
- 结果复核、完成筛选、AI 配置、考试监控的 **HTTP 端点已在 Gateway 落地**。
- 考试 UI 收口为 `ExamShellView`，子路由 redirect。

### 仍未对齐

- **实现形态是 demo**：状态权威在 `demo_store` 内存，不是 Postgres + 服务边界。
- 结果详情页：**能看，不能修分/归档**（前端未接 review / complete-screening）。
- 考试监控：**无管理端页面**；WebSocket 方案仅设计文档。
- 候选人详情字段：证件照/风险断言基本可用；`self_description`、`awards` 等未独立建模。
- 状态机文案与枚举未冻结，前后端字符串仍有混用。
- Placeholder：考卷列表、风险管理页。

### 生产化主线（不在本目录展开）

去 demo、schema 补齐、仓储落库、Gateway 变薄 BFF、异步解析、MinIO 真存储等，统一跟踪：

`plans/plan-20260709-production-cutover.md`
