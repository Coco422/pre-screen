# 10. 结果中心列表页

- 路由：`/admin/results`
- 页面目标：汇总所有已交卷候选人，按提交时间和风险等级进入复核。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/results` | 建议扩展 | 结果列表和筛选 |

## 推荐筛选参数

- `task_id`
- `role`
- `status`
- `risk_level`
- `submitted_from`
- `submitted_to`
- `sort_by=submitted_at|total_score|risk_level`
- `order=desc|asc`
- `page`
- `page_size`

## 列表关键字段

- `result_id`
- `candidate_id`
- `candidate_name`
- `role`
- `submitted_at`
- `total_score`
- `objective_score`
- `coding_score`
- `subjective_suggested_score`
- `risk_level`
- `review_status`

## 页面规则

- 列表默认按 `submitted_at desc` 排序。
- 如果是“已交卷待复核”视角，默认筛选 `review_status=pending`。
- 当前仓库里的结果列表只有 `candidate_name`、`role`、`submitted_at`、`total_score`，离真实复核页还差客观题、代码题、主观题建议分和风险等级。
