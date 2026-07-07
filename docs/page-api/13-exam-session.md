# 13. 在线作答页

- 路由：`/exam/:token/session`
- 页面目标：稳定作答、自动保存、记录风控事件、支持代码题运行和提交。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/public/exams/{token}` | 已有 | 读取考试题目、剩余时间、已有草稿 |
| `POST` | `/api/public/exams/{token}/heartbeat` | 已有 | 保活和在线状态上报 |
| `PUT` | `/api/public/exams/{token}/answers/{questionId}` | 已有 | 自动保存答案 |
| `POST` | `/api/public/exams/{token}/risk-events` | 已有 | 记录失焦、切页、复制粘贴、断网恢复等事件 |
| `POST` | `/api/public/exams/{token}/coding/run` | 已有 | 代码题试运行 |
| `POST` | `/api/public/exams/{token}/coding/submit` | 已有 | 代码题正式评测 |
| `POST` | `/api/public/exams/{token}/submit` | 建议扩展 | 正式交卷或超时自动交卷 |

## 页面规则

- 页面初始化先调用 `GET /api/public/exams/{token}`。
- 自动保存用 `PUT /answers/{questionId}`，接口必须幂等。
- 心跳和风控事件独立上报，不要和保存答案绑在一起。
- 代码题的“运行”与“提交评测”必须分开。
- `POST /api/public/exams/{token}/submit` 建议支持 `submit_reason=manual|timeout|disconnect_recovery`，方便审计。

## 风控事件建议枚举

- `window_blur`
- `page_hidden`
- `copy`
- `paste`
- `network_offline`
- `network_online`

## 与当前代码的差异

- 当前公开考试接口基本齐了。
- 还差的是交卷原因、超时自动交卷语义，以及更明确的审计字段。
