# 07. 候选人详情页

- 路由：`/admin/candidates/:candidateId`
- 页面目标：集中查看候选人原始简历、结构化画像、风险提示和下一步动作。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/candidates/{candidateId}` | 建议扩展 | 拉取候选人完整详情 |
| `GET` | `/api/admin/candidates/{candidateId}/resume-preview` | 建议新增 | 拉取简历缩略预览和证件照 |
| `POST` | `/api/admin/candidates/{candidateId}/reject` | 建议新增 | 标记淘汰 |

## 详情页必须拿到的字段

- 基础信息：`name`、`role`、`email`、`phone`、`city`
- 简历原始信息：`photo_url`、`resume_file_url`、`self_description_raw`、`project_experiences_raw[]`、`awards_raw[]`
- 结构化结果：`skills[]`、`years_of_experience`、`project_summary`、`match_score`
- 风险分析：`risk_flags[]`、`suspicious_claims[]`、`evidence_required_points[]`
- 业务索引：`paper_id`、`paper_status`、`invitation_token`、`result_id`

## 页面规则

- 左栏看基础信息和简历预览，中栏看结构化档案，右栏看风险和动作。
- 这个页面的重点是“看人”和“做判断”，不应该把编辑逻辑塞进来。
- 当前仓库的候选人详情已经有 `projects` 和 `analysis`，但还缺你明确提到的证件照、自我描述、比赛获奖经历、原始断言证据这些字段。
