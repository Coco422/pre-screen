# 18. 系统设置 / 账号 / 通知（UX 设计）

> 更新：2026-07-09  
> 原则：功能 → 前端 UI → 后端实现 → 数据库，而不是只补接口。

## 信息架构

侧栏入口：**系统设置**（原「AI 配置」）→ 路由 `/admin/settings?tab=...`

| Tab | 路由 query | 状态 | 说明 |
|-----|------------|------|------|
| AI 模型 | `tab=ai` | ✅ 已实现 | 原 AI 配置表单作为子面板 |
| 账号与安全 | `tab=account` | 📋 规划 | 头像、显示名、改密、会话 |
| 消息通知 | `tab=notifications` | 📋 规划 | 站内通知与订阅开关 |

顶栏：

| 控件 | 现状 | 目标 |
|------|------|------|
| 铃铛 | 假徽章，点击进通知 tab 说明页 | 未读数 + 通知中心抽屉/页 |
| 用户菜单「账号设置/修改密码」 | 跳转 account tab 占位 | 真实表单 + API |
| 退出登录 | ✅ | 保持 |

## 账号与安全（规划）

### 用户故事

1. HR 上传/更换头像，顶栏与下拉展示。
2. 修改显示名。
3. 修改密码：校验当前密码 → 新密码两次确认 → 刷新 session。
4. 查看活跃会话，可「踢下线」。

### API（建议）

| Method | Path | 用途 |
|--------|------|------|
| `GET` | `/api/admin/settings/profile` | 当前用户资料（含 avatar url） |
| `PUT` | `/api/admin/settings/profile` | 更新显示名等 |
| `POST` | `/api/admin/settings/avatar` | 上传头像 → MinIO |
| `POST` | `/api/admin/settings/password` | 改密 |
| `GET` | `/api/admin/settings/sessions` | 会话列表 |
| `DELETE` | `/api/admin/settings/sessions/:id` | 注销指定会话 |

### 数据

- `auth.users`：+ `avatar_object_key`, `display_name`（已有）
- `auth.sessions`：已有 token_hash / expires_at

## 消息通知（规划）

### 用户故事

1. 解析完成、考卷生成完成、候选人交卷、高风险事件 → 站内通知。
2. 顶栏未读数；点击进入列表并可跳转任务/结果/监控。
3. 设置页可按类型开关。

### API（建议）

| Method | Path | 用途 |
|--------|------|------|
| `GET` | `/api/admin/notifications` | 列表 + unread |
| `POST` | `/api/admin/notifications/:id/read` | 已读 |
| `PUT` | `/api/admin/settings/notification-prefs` | 订阅偏好 |

### 数据（建议新表 `app.notifications`）

- id, user_id, type, title, body, target_url, read_at, created_at

## 实现顺序建议

1. 系统设置壳 + AI 子页（✅ 本切片）
2. 改密 + profile API（依赖 auth 落库）
3. 通知表 + 事件写入点（parse 完成 / paper 完成 / submit）
4. 顶栏真实未读
