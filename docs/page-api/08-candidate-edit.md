# 08. 编辑画像页

- 路由：`/admin/candidates/:candidateId/edit`
- 页面目标：人工修正自动提取结果，确认候选人画像后再进入拟出卷或发卷。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/candidates/{candidateId}` | 建议扩展 | 加载待编辑的候选人详情 |
| `PUT` | `/api/admin/candidates/{candidateId}` | 已有 | 保存人工修正后的画像 |
| `POST` | `/api/admin/candidates/{candidateId}/confirm-profile` | 建议新增 | 明确将候选人推进到拟出卷阶段 |

## 页面保存内容

- 基础字段：`name`、`email`、`phone`、`city`
- 结构化字段：`skills[]`、`project_summary`、`projects[]`
- 备注字段：`review_notes[]`
- 可选补充：`awards[]`、`self_description`、`evidence_required_points[]`

## 页面规则

- `PUT /api/admin/candidates/{candidateId}` 只负责保存编辑结果，不建议隐式推进状态。
- 如果 HR 点击“确认画像并进入拟出卷”，再调用 `POST /api/admin/candidates/{candidateId}/confirm-profile`。
- 这样可以把“保存草稿”和“推进流程”两个动作拆开，避免误操作。
