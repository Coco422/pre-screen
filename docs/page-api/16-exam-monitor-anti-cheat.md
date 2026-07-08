# 16. 考试实时监控与防作弊

- 路由：`/admin/monitor`
- 页面目标：管理员实时查看所有进行中考试的状态，发现异常行为及时干预。

## 实时连接设计

### 架构

```
考生浏览器 ←→ WebSocket(/ws/exam/:token) ←→ Gateway ←→ Monitor Hub
管理员浏览器 ←→ WebSocket(/ws/admin/monitor) ←→ Gateway ←→ Monitor Hub
```

- 考生端：已有心跳 + 风控事件上报（HTTP），升级为 WebSocket 双向通道
- 管理员端：新增 WebSocket 连接，实时推送所有考生状态变化

### 考生 WebSocket 消息

| 方向 | 类型 | 用途 |
|------|------|------|
| 客户端→服务端 | `heartbeat` | 替代 HTTP 心跳，降低延迟 |
| 客户端→服务端 | `risk_event` | 风控事件实时上报 |
| 客户端→服务端 | `answer_sync` | 答案增量同步 |
| 服务端→客户端 | `ack` | 确认收到 |
| 服务端→客户端 | `time_warning` | 剩余 10 分钟/5 分钟提醒 |
| 服务端→客户端 | `force_submit` | 超时强制交卷 |

### 管理员监控面板

| 字段 | 来源 |
|------|------|
| 候选人姓名 | exam session |
| 当前状态（作答中/离线/已交卷） | WebSocket 连接状态 |
| 已答题数 / 总题数 | answer_sync 事件 |
| 最近心跳时间 | heartbeat 事件 |
| 风控事件计数 + 最近事件 | risk_event 聚合 |
| 剩余时间 | 服务端计算 |
| 异常标记（高风险） | 规则引擎判定 |

### 防作弊机制

#### 请求伪造防护

| 层面 | 措施 |
|------|------|
| Token 安全 | 考试 token 为一次性随机串，绑定候选人 + 考卷，过期自动失效 |
| WebSocket 鉴权 | 连接时验证 token + verification_code，建立后通过 session_id 标识 |
| 请求签名 | 每条 WebSocket 消息附带 `timestamp + nonce + HMAC(session_secret, payload)`，防重放 |
| IP 绑定 | 开考后绑定 IP，IP 变化记录为风控事件，频繁变化自动锁定 |
| 设备指纹 | 收集 User-Agent / 屏幕分辨率 / 时区，开考后变化视为异常 |

#### 行为检测

| 检测项 | 规则 | 动作 |
|--------|------|------|
| 心跳中断 | 连续 3 次心跳超时（>45s 无消息） | 标记离线，超过 5 分钟自动交卷 |
| 频繁切屏 | 5 分钟内切屏 >5 次 | 升级为高风险，管理员收到推送 |
| 复制粘贴 | 粘贴内容长度 >200 字符 | 记录内容哈希，标记可能外部输入 |
| 网络切换 | 考试期间 IP 变化 >2 次 | 标记异常，管理员决定是否继续 |
| 答案提交速度 | 客观题 <3s 完成 | 标记疑似随机作答 |
| 代码提交模式 | 一次性粘贴大量代码（非逐步编写） | 记录编辑历史对比 |

#### 管理员干预能力

| 操作 | 效果 |
|------|------|
| 强制交卷 | 服务端发 `force_submit`，考生端自动提交 |
| 暂停考试 | 暂停计时，考生看到"管理员暂停"提示 |
| 延长时间 | 对个别考生增加考试时长 |
| 标记无效 | 将本次考试结果标记为无效 |

### 接口

| Method | Path | 用途 |
|--------|------|------|
| `GET` | `/api/admin/monitor/sessions` | 获取所有活跃考试会话 |
| `GET` | `/api/admin/monitor/sessions/:sessionId` | 单个会话详情 |
| `POST` | `/api/admin/monitor/sessions/:sessionId/force-submit` | 强制交卷 |
| `POST` | `/api/admin/monitor/sessions/:sessionId/pause` | 暂停 |
| `POST` | `/api/admin/monitor/sessions/:sessionId/extend` | 延长时间 |
| `POST` | `/api/admin/monitor/sessions/:sessionId/invalidate` | 标记无效 |
| WebSocket | `/ws/admin/monitor` | 实时事件流 |
| WebSocket | `/ws/exam/:token` | 考生双向通道 |

### 实现优先级

1. **P0**: HTTP 心跳 + 风控事件已有，先做管理员只读监控面板（轮询 `/admin/monitor/sessions`）
2. **P1**: 考生端升级为 WebSocket，管理员面板实时推送
3. **P2**: 防作弊规则引擎 + 干预能力
