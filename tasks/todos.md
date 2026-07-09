# Deferred Goal Ledger

> **Status**: Backlog  
> **Updated**: 2026-07-09  
> **Scope**: Medium/long-term goals deferred from active plan execution

Current plan tasks live in the active plan's `## Task Breakdown`  
（`plans/plan-20260709-production-cutover.md`）。  
Do not duplicate that execution checklist here. Record only work intentionally deferred beyond this slice, with the tradeoff and revisit trigger.

## Deferred Goals

| Goal | Why Deferred | Tradeoff | Revisit Trigger |
|------|--------------|----------|-----------------|
| **站内消息通知中心**（顶栏铃铛真实未读） | 先做解析/出题长任务与主链路；设计见 `docs/page-api/18-system-settings-and-account.md` | 顶栏仍为占位入口 | 长任务稳定后，HR 需要「完成提醒」 |
| **账号设置**：头像 / 显示名 / 改密 / 会话管理 | 依赖 auth 落库与 MinIO 头像；系统设置 account tab 已占位 | 暂用 bootstrap 账号 | `STORE_BACKEND=postgres` 成为默认后 |
| WebSocket 考试监控 / Monitor Hub | HTTP 轮询足够支撑第一版监控页；WS 改动面大 | 实时性差一点 | 监控页上线后，HR 反馈延迟不可接受 |
| 高级防作弊（设备指纹、HMAC、IP 绑定） | 首期只需留痕 + 人工判断 | 误伤与产品复杂度 | 批量作弊投诉或对公网开放考试 |
| 多租户 / SSO / 细粒度 RBAC | 当前单 HR 团队内网 | 无法 SaaS 化 | 第二个组织要独立数据隔离 |
| 题库运营后台（独立题库 CRUD/版本） | 现用模板 + 生成器 + JSON 题足够 | 运营改题依赖发版/SQL | 题目量上升、多岗位模板频繁改 |
| 独立微服务进程网格（全服务 HTTP） | cutover 先仓储落库；进程拆分可后置 | 部署拓扑暂时仍偏「gateway 重」 | 需独立扩缩 parse worker 之外的服务 |
| `regenerate-llm-questions` 单接口 | 非主链路阻塞 | HR 需整卷重生成 | 出题返工频繁 |
| 候选人状态 10 态细粒度 UI 全量替换 | 枚举已冻结，UI 逐步切换 | 文案与筛选短暂混用 | 全站文案 sweep |
| 考卷版本 diff / 模板库管理 | 列表+编辑器已覆盖 MVP | 无法对比历史草稿 | 同一候选人多次出卷 |
