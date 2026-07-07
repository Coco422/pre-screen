# 14. 交卷完成页

- 路由：`/exam/:token/submitted`
- 页面目标：明确告知候选人已提交成功，不再展示复杂内容。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/public/exams/{token}` | 已有 | 读取交卷后的提交结果摘要 |
| `GET` | `/api/public/exams/{token}/submission-summary` | 建议新增 | 只返回提交完成页需要的信息 |

## 页面关键字段

- `submitted_at`
- `paper_title`
- `candidate_name`
- `submission_summary`

## 页面规则

- 这个页面不需要重新拉整张试卷内容。
- 如果继续复用 `GET /api/public/exams/{token}`，提交后最好只返回摘要，不再返回完整题目。
- 更稳妥的方式是新增 `GET /api/public/exams/{token}/submission-summary`，专门给完成页使用。
