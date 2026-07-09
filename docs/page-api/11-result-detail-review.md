# 11. 结果详情与评分复核页

- 路由：`/admin/results/:resultId`
- 页面目标：查看答卷证据、修正 AI 不合理评分、确认是否通过筛选并归档。
- 对齐更新：2026-07-09

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/results/{resultId}` | 已有 | 拉取结果详情、评分拆解、风险摘要 |
| `PUT` | `/api/admin/results/{resultId}/review` | 已有 / **前端未接** | 保存 HR 修分和复核备注 |
| `POST` | `/api/admin/results/{resultId}/complete-screening` | 已有 / **前端未接** | 最终通过筛选或淘汰，并写归档结果 |

## 详情页必须拿到的字段

- 候选人信息：`candidate_id`、`name`、`role`
- 总分拆解：`objective_score`、`coding_score`、`subjective_ai_score`、`subjective_final_score`、`total_score`
- 作答内容：基础信息题、客观题、主观题、代码题原答案
- 代码运行结果：`passed_count`、`failed_count`、`test_cases[]`
- 风险证据：`risk_events[]`、`risk_summary`
- 复核状态：`review_status`、`reviewed_by`、`reviewed_at`

## 已落地接口约定（Gateway demo_store）

- `PUT /api/admin/results/{resultId}/review`
  - 请求体：`final_subjective_score?`、`review_notes[]?`、`risk_override?`
  - 响应：更新后的 result；`review_status` 置为 `reviewed`
- `POST /api/admin/results/{resultId}/complete-screening`
  - 请求体：`decision=pass|reject`、`review_notes[]?`
  - 响应：更新后的 result / 候选人归档相关字段

> 生产化落库后契约保持稳定；内部从 demo_store 迁到 scoring/exam 表，对外 path 不变。

## 页面规则

- 候选人交卷后，先进入 `已交卷`，不要直接算成 `已完成筛选`。
- HR 在这个页面修分时，候选人状态建议变成 `评分复核中`。
- 点击「通过筛选」后，再调用 `complete-screening`，将候选人推进为 `已完成筛选`，同时写入归档。
- 如果点击「淘汰」，也走 `complete-screening`，但 `decision=reject`。

## 与当前代码的差异

- **后端**：review / complete-screening 已在 Gateway 实现（2026-07-08）。
- **前端**：`ResultDetailView` 仍以查看为主，未调用上述写接口。
- **数据形态**：结果仍在 demo_store 内存；重启丢失；风险时间线完整度依赖 store 内 seed/提交路径。
- **待办**：前端接线列入 `plans/plan-20260709-production-cutover.md` 的产品补齐切片；持久化列入同一 plan 的 scoring 切片。
