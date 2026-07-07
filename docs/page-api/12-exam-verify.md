# 12. 考试身份验证页

- 路由：`/exam/:token/start`
- 页面目标：候选人看到岗位、考试名称、时长、验证码输入框，尽快进入考试。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/public/exams/{token}` | 已有 | 读取考试入口基础信息 |
| `POST` | `/api/public/exams/{token}/start` | 已有 | 校验验证码并正式开考 |

## 页面关键字段

- `paper_title`
- `candidate_name`
- `duration_minutes`
- `instructions`
- `state=not_started|in_progress|submitted`

## 页面规则

- 页面文案只保留岗位、考试名称、时长、验证码和极短规则。
- 输入验证码并点击“开始考试”时，调用 `POST /api/public/exams/{token}/start`。
- 如果 token 已经开始过，`GET /api/public/exams/{token}` 应能返回当前状态，前端可直接跳转到 `/session` 或 `/submitted`。
