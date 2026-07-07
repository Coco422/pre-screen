# 01. 登录页

- 路由：`/login`
- 页面目标：完成 HR 登录并恢复已有会话。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `POST` | `/api/admin/session/login` | 已有 | 账号密码登录 |
| `GET` | `/api/admin/session/me` | 已有 | 刷新页面时恢复登录态 |

## 页面使用方式

- `POST /api/admin/session/login`
  - 请求体：`{ "username": "...", "password": "..." }`
  - 关键响应：`token/session_token`、`user_name/display_name`、`role`
- `GET /api/admin/session/me`
  - 请求头：`Authorization: Bearer <token>`
  - 关键响应：当前用户基础信息，用于刷新后自动进入后台

## 页面规则

- 登录成功后跳转 `/admin/dashboard`。
- 登录页本身不需要额外的业务接口。
- “忘记密码”如果后续要做成真实能力，再单独补 `/api/admin/session/password-reset`，当前可以先不做。
