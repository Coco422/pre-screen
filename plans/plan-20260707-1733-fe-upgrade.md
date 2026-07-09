# Plan: 前端文案精简 + 功能梳理 + 布局优化

> **Status**: Done
> **Created**: 20260707-1733
> **Completed**: 2026-07-08
> **Slug**: fe-upgrade
> **Artifact Level**: work-package
> **Promotion Reason**: 前端体验与产品语气不匹配，功能边界不清晰
> **Verification Boundary**: `pnpm --filter web build` 通过 + 手动浏览各页面无文案遗漏
> **Rollback Surface**: git revert 单 commit
> **Spec**: `docs/spec.md`
> **Evidence**: commits `6310544`, `f851651`, `e207d98` 等（strip verbose copy / simplify layout）

## 问题摘要

当前前端所有页面充斥产品叙事文案（「把初筛流程收进一条干净的工作流」「面向 HR 的第一页不是表格堆砌」等），像在读产品文档而不是在用工具。需要全部替换为极简工具型文案，同时梳理清楚现有功能边界和布局冗余。

---

## 一、现有页面/功能清单

| 路由 | 组件 | 功能 | 状态 |
|------|------|------|------|
| `/admin/candidates` | CandidateListView | 候选人列表、搜索/筛选、批量共性分析面板、指标统计 | Working（接 Gateway，有 fallback） |
| `/admin/candidates/:id` | CandidateDetailView | 候选人画像详情、解析指标、下一步动作 | Working |
| `/admin/papers/:id` | PaperEditorView | 考卷草稿预览、题目结构 outline | Working（只读，编辑按钮是 stub） |
| `/exam/:token` | ExamShellView | 考试主壳：倒计时、题目导航、风控事件、心跳、自动保存 | Working |
| — | ExamQuestionPanel | 基础信息/客观题/主观题作答 | Working |
| — | CodeQuestionPanel | 代码题编辑器 + 试跑 + 提交判题 | Working |
| — | AdminLayout | 侧边栏壳（导航 + 全局指标） | Working（导航硬编码 demo 路由） |

**Stub / 半成品**:
- PaperEditorView 的「保存草稿」「生成链接与验证码」按钮无绑定
- AdminLayout 的「新建筛选任务」按钮无绑定
- AdminLayout sidebar 导航硬编码了 c-001 / p-001
- CandidateListView 搜索框和 select 筛选无实际功能

---

## 二、文案改造清单

### 原则
- 去掉所有产品叙事、自我描述、情感渲染
- 只保留操作提示（极简）或留空
- pill 标签改为功能性标识（中文短词）

### 逐组件改造

| 组件 | 位置 | 原文案 | 改为 |
|------|------|--------|------|
| AdminLayout | sidebar `.pill` | "HR Console" | "控制台" |
| AdminLayout | sidebar h1 | "Pre-Screen Studio" | "初筛工作台" |
| AdminLayout | sidebar `.section-copy` | "从简历接收到考卷发出，把初筛流程收进一条干净的工作流。" | **删除** |
| AdminLayout | header `.pill` | "Hiring Ops" | "当前" |
| AdminLayout | header h2 | "技术岗初筛控制台" | "候选人概览"（或根据路由动态） |
| CandidateListView | hero `.pill` | "Pipeline Snapshot" | "筛选池" |
| CandidateListView | hero h2 | "把 PDF、画像、考卷草稿放到一个工作台里。" | "候选人" |
| CandidateListView | hero `.hero-copy` | "面向 HR 的第一页不是表格堆砌..." | **删除** |
| CandidateListView | loading state `.section-copy` | "Gateway 已接入，列表会优先读取后端返回..." | "加载中" |
| CandidateListView | batch analysis `.pill` | "Batch Analysis" | "批量分析" |
| CandidateDetailView | loading `.section-copy` | "如果 Gateway 暂不可用，页面会自动回退到本地样例数据。" | "加载中" |
| CandidateDetailView | `.pill` | "Candidate Profile" / "Resume Intelligence" | "候选人" / "解析详情" |
| PaperEditorView | `.pill` | "Paper Draft" | "考卷草稿" |
| PaperEditorView | `.section-copy` | "模板为主 + JD 微调。HR 可以在发卷前调整..." | **删除** |
| PaperEditorView | loading `.section-copy` | "编辑器优先读取 Gateway 返回的草稿详情..." | "加载中" |
| ExamShellView | sidebar `.pill` | "Candidate Session" | "考试" |
| ExamShellView | sidebar `.section-copy` | "自动保存已启用，后端心跳为准。切页、失焦等轻量风控事件会记录。" | **删除** |
| ExamShellView | intro card `.pill` | "Exam Flow" | "提示" |
| ExamShellView | intro card h2 | "先补基础信息，再完成客观题、主观题和代码题。" | "按顺序完成各题即可" |
| ExamShellView | intro card `.section-copy` | "这不是冷冰冰的表单页..." | **删除** |
| ExamShellView | loading `.section-copy` | "题目会优先从 Gateway 加载，异常时回退到本地兜底数据。" | "正在加载题目" |

---

## 三、布局优化

| 变更 | 理由 |
|------|------|
| CandidateListView: 删掉 `.list-hero` 的 `.grid-two` 嵌套 `hero-title` + `hero-copy` 区，metrics 直接平铺在顶部 | 不需要"英雄区"讲故事，指标到位就行 |
| ExamShellView: 移除 `.intro-card` 整个 section（或缩为一行灰色提示） | 考生不需要读说明文，直接看题 |
| PaperEditorView: 删掉 head 区的叙事 `<p>` | 编辑器不需要解释自己是什么 |
| AdminLayout: sidebar footer 的 "92% 自动流程完成度" metric 目前硬编码，要么接真实数据，要么删掉 | 假数据不如没有 |

---

## 四、Task Breakdown

- [x] 1. AdminLayout：文案精简 + 删除 sidebar 叙事段落 + 删除硬编码 metric
- [x] 2. CandidateListView：砍 hero 叙事区、重构顶部为纯 metrics 行、pill/loading 文案替换
- [x] 3. CandidateDetailView：pill 文案替换 + loading 文案精简
- [x] 4. PaperEditorView：删 head 叙事 + pill 中文化 + loading 精简
- [x] 5. ExamShellView：删 intro-card section + sidebar 叙事删除 + pill 中文化
- [x] 6. 验证 build 通过 + 各页面视觉检查无残留碎碎念

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| 删文案后某些区块视觉空洞 | 中 | 低 | 布局优化同步调整间距和结构 |
| 改 pill 标签后 CSS 选择器依赖类名 | 低 | 低 | pill 是内容不是 class，CSS 不受影响 |

## Promotion Gate

- **Merge/PR unit**: 单 commit `feat(web): strip verbose copy, simplify layout`
- **Rollback surface**: `git revert`
- **Verification boundary**: build + 手动浏览 4 条路由
