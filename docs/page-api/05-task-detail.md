# 05. 任务详情与上传简历页

- 路由：`/admin/tasks/:taskId`
- 页面目标：上传 PDF 简历，跟踪信息提取和整理进度，进入候选人详情或发卷。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/tasks/{taskId}` | 已有 | 任务详情、上传记录、候选人列表 |
| `POST` | `/api/admin/tasks/{taskId}/uploads` | 已有 | 批量上传 PDF 简历 |
| `GET` | `/api/admin/uploads/{uploadId}` | 已有 | 单个上传任务轮询 |

## 上传后真实处理链路

- 第一步：保存 PDF 原件，创建上传记录和候选人占位。
- 第二步：调用 PyMuPDF 提取文本层和分页信息。
- 第三步：必要时对低文本覆盖页做多模态补读，提取证件照、项目经历、自我描述、比赛获奖经历等原始信息。
- 第四步：调用 LLM 做信息整理和风险断言，识别空洞表述，例如“做了某优化、性能提升 50%”但缺少真实佐证。
- 第五步：整理完成后进入 `拟出卷中/待发卷`。

## 推荐返回字段

- 上传记录需要有：`upload_id`、`file_name`、`resume_uploaded_at`、`status`、`progress`、`processing.stage`、`processing.message`
- 候选人卡片需要有：`candidate_id`、`name`、`status`、`risk_flag_count`、`paper_status`、`next_action`

## 页面规则

- 页面轮询可以继续复用 `GET /api/admin/tasks/{taskId}`，不一定非要拆单独监控接口。
- 但如果后续上传量大，建议再补 `GET /api/admin/tasks/{taskId}/processing-summary`，只返回轻量监控数据。
- 这个页面是 PDF 上传的真正入口，不建议把上传能力塞到新建任务页里。
