# 06. 候选人列表页

- 路由：`/admin/candidates`
- 页面目标：高频筛选页，快速定位待审核、待发卷、已发卷、已交卷候选人。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/candidates` | 已扩展 | 候选人列表和多条件筛选 |

## 推荐筛选参数

- `task_id`
- `role`
- `status`
- `pending_review=true|false`
- `paper_sent=true|false`
- `paper_status=draft|ready|published`
- `risk_level=low|medium|high`
- `keyword`
- `sort_by=updated_at|resume_uploaded_at|submitted_at`
- `order=asc|desc`
- `page`
- `page_size`

## 列表关键字段

- `candidate_id`
- `name`
- `role`
- `resume_parse_status`
- `screening_status`
- `risk_flag`
- `risk_level`
- `resume_uploaded_at`
- `paper_sent`
- `updated_at`
- `next_action`
- `paper_id`
- `result_id`

## 页面规则

- 候选人列表页要能直接根据首页和任务页带参跳转，例如 `?status=待发卷`、`?task_id=t-001`。
- “是否待审核”和“是否已发卷”最好做成显式布尔筛选，不要完全依赖状态字符串。
- 当前仓库里的 `GET /api/admin/candidates` 只有 `task_id` 和 `status` 两个参数，实际业务还不够用。
