# 09. 考卷编辑与发布页

- 路由：`/admin/papers/:paperId`
- 页面目标：基于候选人简历生成题目草稿，人工复核后正式发卷。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `POST` | `/api/admin/candidates/{candidateId}/papers/generate` | 已有 | 为候选人生成考卷草稿 |
| `GET` | `/api/admin/papers/{paperId}` | 已有 | 获取考卷草稿详情 |
| `PUT` | `/api/admin/papers/{paperId}` | 已有 | 编辑题目、分值、时长等 |
| `POST` | `/api/admin/papers/{paperId}/publish` | 已有 | 生成考试链接和验证码 |
| `POST` | `/api/admin/papers/{paperId}/regenerate-llm-questions` | 建议新增 | 仅重生成人简历相关题目 |

## 页面关键字段

- 考卷概览：`title`、`duration_minutes`、`mix`
- 题目列表：`question_id`、`kind`、`title`、`description`、`score`、`required`
- 生成说明：`generation_summary.matched_projects`、`focus_topics`、`generation_notes`
- 发布结果：`token`、`verification_code`、`exam_url`、`published_at`

## 页面规则

- 必问题和题库随机题可以直接由后端生成。
- 针对简历内容的定制题应该保留 `question_source=llm_resume_based` 之类的来源字段，便于 HR 识别。
- 如果 LLM 在信息整理阶段已经标记了“性能提升 50% 但缺证据”之类风险点，出题接口应把这些风险点转成追问题。
- 发布成功后候选人状态要从 `待发卷` 变成 `已发卷`。

## 与当前代码的差异

- 当前已有生成、读取、编辑、发布考卷接口。
- 但还缺“只重生成人题”的能力，也缺“题目来源”和“追问理由”这两个对 HR 很重要的字段。
