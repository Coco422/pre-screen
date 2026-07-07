# 02. HR 工作台

- 路由：`/admin/dashboard`
- 页面目标：3 秒内判断先处理谁，再进入候选人、发卷或结果复核。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/dashboard` | 建议新增 | 返回顶部指标和三个核心列表 |
| `GET` | `/api/admin/candidates?status=信息整理中&sort_by=resume_uploaded_at&order=asc&limit=10` | 建议扩展 | 展示筛选中候选人，越早上传越靠前 |
| `GET` | `/api/admin/candidates?status=待发卷&sort_by=profile_completed_at&order=asc&limit=10` | 建议扩展 | 展示待出卷候选人 |
| `GET` | `/api/admin/results?status=已交卷&sort_by=submitted_at&order=desc&limit=10` | 建议扩展 | 展示最近已交卷候选人 |

## 推荐主接口结构

- `GET /api/admin/dashboard`
  - 返回指标：`screening_candidate_count`、`pending_publish_count`、`exam_in_progress_count`、`submitted_count`、`screening_completed_count`
  - 返回列表：`screening_candidates[]`、`pending_publish_candidates[]`、`submitted_results[]`

## 页面规则

- “筛选中候选人”按 `resume_uploaded_at asc` 排序，避免老简历被遗漏。
- “待出卷候选人”按 `profile_completed_at asc` 排序，优先推进已经整理完信息的人。
- “已交卷人”按 `submitted_at desc` 排序，方便 HR 先看最新交卷结果。
- “查看全部”统一跳转到候选人列表或结果中心，并带上对应筛选参数。

## 与当前代码的差异

- 当前仓库没有 `dashboard` 聚合接口，前端是通过 `loadTasks()`、`loadCandidates()`、`loadResults()` 自己拼。
- 按你现在的流程，首页不应该把“最近任务”作为核心区块，而应该换成“筛选中候选人 / 待出卷候选人 / 已交卷人”。
