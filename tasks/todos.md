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
| WebSocket 考试监控 / Monitor Hub | HTTP 轮询足够支撑第一版监控页；WS 改动面大 | 实时性差一点，实现简单 | production-cutover Phase 4 监控页上线后，HR 反馈延迟不可接受 |
| 高级防作弊（设备指纹、HMAC、IP 绑定策略引擎） | 首期只需留痕 + 人工判断 | 误伤与产品复杂度 | 出现批量作弊投诉或对公网开放考试 |
| 多租户 / SSO / 细粒度 RBAC | 当前单 HR 团队内网 | 无法 SaaS 化 | 第二个组织要独立数据隔离 |
| 题库运营后台（独立题库 CRUD/版本） | 现用模板 + 生成器 + JSON 题足够 | 运营改题依赖发版/SQL | 题目量上升、多岗位模板频繁改 |
| 独立微服务进程网格（全服务 HTTP） | cutover 先仓储落库；进程拆分可后置 | 部署拓扑暂时仍偏「gateway 重」 | 团队要独立扩缩 parse worker 之外的服务 |
| `regenerate-llm-questions` 单接口 | 非主链路阻塞 | HR 需整卷重生成 | 出题返工频繁 |
| 考卷列表页 / 风险专页（非 Placeholder） | 编辑器与结果/监控可覆盖 | 导航入口弱 | 试卷资产量变大需要检索 |
| 候选人状态 10 态细粒度 UI | 先冻结枚举再全量改文案 | 文案与筛选短暂不一致 | Phase 0 状态机文档合并后 |
