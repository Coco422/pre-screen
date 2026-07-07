# 11. 结果详情与评分复核页

- 路由：`/admin/results/:resultId`
- 页面目标：查看答卷证据、修正 AI 不合理评分、确认是否通过筛选并归档。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/results/{resultId}` | 建议扩展 | 拉取结果详情、评分拆解、风险时间线 |
| `PUT` | `/api/admin/results/{resultId}/review` | 建议新增 | 保存 HR 修分和复核备注 |
| `POST` | `/api/admin/results/{resultId}/complete-screening` | 建议新增 | 最终通过筛选或淘汰，并写归档结果 |

## 详情页必须拿到的字段

- 候选人信息：`candidate_id`、`name`、`role`
- 总分拆解：`objective_score`、`coding_score`、`subjective_ai_score`、`subjective_final_score`、`total_score`
- 作答内容：基础信息题、客观题、主观题、代码题原答案
- 代码运行结果：`passed_count`、`failed_count`、`test_cases[]`
- 风险证据：`risk_events[]`、`risk_summary`
- 复核状态：`review_status`、`reviewed_by`、`reviewed_at`

## 推荐新增接口定义

- `PUT /api/admin/results/{resultId}/review`
  - 请求体建议包含：`manual_scores[]`、`final_subjective_score`、`review_notes[]`、`risk_override`
  - 响应建议返回：`review_status=reviewing|reviewed`、`final_total_score`
- `POST /api/admin/results/{resultId}/complete-screening`
  - 请求体建议包含：`decision=pass|reject`、`review_notes[]`
  - 响应建议返回：`candidate_status`、`archive_id`、`completed_at`

## 页面规则

- 候选人交卷后，先进入 `已交卷`，不要直接算成 `已完成筛选`。
- HR 在这个页面修分时，候选人状态建议变成 `评分复核中`。
- 点击“通过筛选”后，再调用 `complete-screening`，将候选人推进为 `已完成筛选`，同时写入归档。
- 如果点击“淘汰”，也走 `complete-screening`，但 `decision=reject`。

## 与当前代码的差异

- 当前仓库只有 `GET /api/admin/results/{resultId}` 的查看能力。
- 真实流程里最关键的“修分”和“通过筛选后归档”还没有接口，需要在这里补齐。
