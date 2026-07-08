# Pre-Screen 接口对齐审计

> 审计时间：2026-07-07
> 对比来源：`docs/page-api/*.md` vs 实际 `admin.py` + `public_exam.py` + `demo_store.py`

## 对齐结果

### ✅ 已有且可用

| 文档页面 | 接口 | 后端实现 |
|----------|------|----------|
| 01-login | `POST /admin/session/login` | ✅ demo_store.login() |
| 01-login | `GET /admin/session/me` | ✅ demo_store.get_current_user() |
| 02-dashboard | `GET /admin/dashboard` | ✅ demo_store.get_dashboard() |
| 03-task-list | `GET /admin/tasks` | ✅ demo_store.list_tasks() |
| 04-task-create | `POST /admin/tasks` | ✅ demo_store.create_task() |
| 05-task-detail | `GET /admin/tasks/:taskId` | ✅ demo_store.get_task() |
| 05-task-detail | `POST /admin/tasks/:taskId/uploads` | ✅ demo_store.create_uploads() |
| 05-task-detail | `GET /admin/uploads/:uploadId` | ✅ demo_store.get_upload() |
| 06-candidate-list | `GET /admin/candidates` | ✅ demo_store.list_candidates() |
| 07-candidate-detail | `GET /admin/candidates/:id` | ✅ demo_store.get_candidate() |
| 07-candidate-detail | `GET /admin/candidates/:id/resume.pdf` | ✅ demo_store.get_candidate_pdf_path() |
| 08-candidate-edit | `PUT /admin/candidates/:id` | ✅ demo_store.update_candidate() |
| 09-paper-editor | `POST /admin/candidates/:id/papers/generate` | ✅ demo_store.generate_paper() |
| 09-paper-editor | `GET /admin/papers/:paperId` | ✅ demo_store.get_paper() |
| 09-paper-editor | `PUT /admin/papers/:paperId` | ✅ demo_store.update_paper() |
| 09-paper-editor | `POST /admin/papers/:paperId/publish` | ✅ demo_store.publish_paper() |
| 10-result-list | `GET /admin/results` | ✅ demo_store.list_results() |
| 11-result-detail | `GET /admin/results/:resultId` | ✅ demo_store.get_result() |
| 12-exam-verify | `GET /public/exams/:token` | ✅ demo_store (get_exam_shell) |
| 12-exam-verify | `POST /public/exams/:token/start` | ✅ demo_store (start_exam) |
| 13-exam-session | `PUT /public/exams/:token/answers/:qId` | ✅ |
| 13-exam-session | `POST /public/exams/:token/heartbeat` | ✅ |
| 13-exam-session | `POST /public/exams/:token/risk-events` | ✅ |
| 13-exam-session | `POST /public/exams/:token/coding/run` | ✅ |
| 13-exam-session | `POST /public/exams/:token/coding/submit` | ✅ |
| 14-exam-submitted | `POST /public/exams/:token/submit` | ✅ |

### ❌ 文档标记"建议新增"但尚未实现

| 文档页面 | 接口 | 用途 | 优先级 |
|----------|------|------|--------|
| 09-paper-editor | `POST /admin/papers/:id/regenerate-llm-questions` | 只重新生成简历相关题目 | P2 |
| 11-result-detail | `PUT /admin/results/:id/review` | HR 修分和复核备注 | P1 |
| 11-result-detail | `POST /admin/results/:id/complete-screening` | 通过/淘汰 + 归档 | P1 |

### ⚠️ 文档标记"建议扩展"

| 文档页面 | 接口 | 差异 | 优先级 |
|----------|------|------|--------|
| 06-candidate-list | `GET /admin/candidates` | 文档要求筛选 paper_status/risk_level 等，当前已支持 status/role/keyword/task_id/pending_review/paper_sent/paper_status/risk_level/sort_by/order | ✅ 已达标 |
| 07-candidate-detail | `GET /admin/candidates/:id` | 文档要求证件照/原始提取结果/风险断言，当前已有 avatar(通过画像)、analysis.risks、projects | ⚠️ 基本达标，缺自我描述/比赛获奖单独字段 |
| 11-result-detail | `GET /admin/results/:id` | 文档要求风险时间线/作答原文/代码运行结果，需确认 demo_store 返回完整度 | ⚠️ 需验证 |

## 结论

**26 个接口中 26 个已有实现，主链路完整闭环。**

待补的 3 个接口（review 修分、complete-screening 归档、regenerate-llm-questions）属于"HR 复核"阶段的增强功能，不阻塞主流程。

## 建议下一步

1. P1：补 `PUT /admin/results/:id/review` + `POST /admin/results/:id/complete-screening`（让 HR 能修分和确认通过）
2. P2：补 `POST /admin/papers/:id/regenerate-llm-questions`（让 HR 能只刷新 AI 生成的题目）
3. P2：候选人详情补 `self_description`、`awards` 字段
4. P3：候选人状态细化为文档建议的 10 种状态
