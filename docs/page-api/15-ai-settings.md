# 15. AI 配置管理

- 路由：`/admin/settings/ai`
- 页面目标：让管理员在前端直接配置 AI 模型连接参数，无需修改环境变量或重启服务。

## 功能设计

### 配置项

| 字段 | 类型 | 说明 |
|------|------|------|
| AI Base URL | string | 模型 API 地址，如 `http://172.16.99.204:3398` |
| AI Model | string | 模型名称，如 `qwen3.6-27b` |
| AI API Key | password | API 密钥，前端掩码显示 |

### 交互

- 表单直接展示当前配置（API Key 掩码）
- 修改后点"保存"，调用 `PUT /admin/settings/ai`
- 保存后提供"连通性测试"按钮，调用 `POST /admin/settings/ai/test`
  - 后端发一个简单 prompt（如"请回复OK"）给模型，返回 `{ ok: true, latency_ms: 120 }` 或 `{ ok: false, error: "connection refused" }`
- 测试通过显示绿色徽章 + 延迟，失败显示红色 + 错误信息

### 接口

| Method | Path | 用途 |
|--------|------|------|
| `GET` | `/api/admin/settings/ai` | 获取当前 AI 配置（key 掩码） |
| `PUT` | `/api/admin/settings/ai` | 更新 AI 配置 |
| `POST` | `/api/admin/settings/ai/test` | 测试连通性 |

### 后端实现

- 配置写入内存 store + `.env` 文件（或数据库），运行时热更新 AIClient 实例
- API Key 存储时加密，GET 时只返回 `sk-****xxxx` 格式
- 测试端点：实例化 AIClient，发 `simple_text_completion("请回复OK")`，计时返回

### 安全

- 仅管理员可访问（需 bearer token）
- API Key 不在任何日志中明文输出
