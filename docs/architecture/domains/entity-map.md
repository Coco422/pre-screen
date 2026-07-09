# Entity map: demo_store → Postgres

> **Updated**: 2026-07-09  
> **Plan**: Phase 0.2

| demo_store field | Schema.table | Notes |
|------------------|--------------|-------|
| `admin_sessions` + hard-coded user | `auth.users`, `auth.sessions` | token 存 hash |
| `tasks` | `app.screening_tasks` | id 保持 `t-xxx` 文本 |
| `uploads` | `resume.upload_jobs` | MinIO key + processing jsonb |
| `candidates` | `resume.candidates` | `external_id` = `c-xxx`；profile jsonb |
| candidate PDF path | `resume.resume_files` + MinIO | local_path 仅缓存 |
| `papers` | `exam.papers` | questions jsonb |
| `exam_tokens` / invitation | `exam.invitations` | access_token + code_hash |
| `sessions` | `exam.sessions` | answers/risk 可 jsonb 过渡 |
| answer drafts | `exam.answer_drafts` | 规范化后可替代 sessions.answers |
| coding submissions | `judge.submissions` | run/submit 轨迹 |
| `results` | `scoring.results` | summary + question_reviews jsonb |
| risk events (session) | `risk.events` | 可从 sessions 双写 |
| `_ai_settings` | `app.ai_settings` | 单行 id=1 |
| OBJECTIVE_DETAILS seed bank | `exam.question_bank` (later) | Phase 3 迁出硬编码 |

## ID strategy

- 对外 ID 保持字符串（`t-001`, `c-001`, `p-001`…）以兼容现有前端。
- 内部可用 bigserial；`external_id` / 文本主键二选一：  
  **本 cutover 采用文本主键**（与 demo API 一致），降低迁移摩擦。
