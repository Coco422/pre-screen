# 15. AI 配置管理

- 文档路由：`/admin/settings/ai`
- **当前前端路由**：`/admin/settings`（`AiSettingsView`）
- 页面目标：让管理员在前端直接配置 AI 模型连接参数，无需改环境变量后整栈重启。
- 对齐更新：2026-07-09

## 功能设计

### 配置项

| 字段 | 类型 | 说明 |
|------|------|------|
| AI Base URL | string | 模型 API 地址，如 `http://172.16.99.204:3398` |
| AI Model | string | 模型名称，如 `qwen3.6-27b` |
| AI API Key | password | API 密钥，前端掩码显示 |

### 交互

- 表单展示当前配置（API Key 掩码）
- 保存调用 `PUT /admin/settings/ai`
- 「测试连通性」调用 `POST /admin/settings/ai/test`
  - 成功：`{ ok: true, latency_ms }`
  - 失败：`{ ok: false, error }`

### 接口

| Method | Path | 状态 | 用途 |
|--------|------|------|------|
| `GET` | `/api/admin/settings/ai` | 已有 | 获取当前 AI 配置（key 掩码） |
| `PUT` | `/api/admin/settings/ai` | 已有 | 更新 AI 配置 |
| `POST` | `/api/admin/settings/ai/test` | 已有 | 测试连通性 |

### 后端实现（当前）

- 配置存在 **Gateway demo_store 内存**；进程重启回退环境变量默认值
- GET 返回掩码 key + `configured` 标志
- test 端点实例化 AIClient 做简单 completion

### 生产化差距

- 配置应落库或加密持久化（非仅内存）
- 多实例共享同一配置源
- Key 加密 at rest；审计日志不落明文
- 与 resume/exam 解析链路共用同一运行时配置源

### 安全

- 仅管理员可访问（需 bearer token）
- API Key 不在日志中明文输出
