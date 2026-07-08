# Plan: 第二轮前端文案/布局精简

> **Status**: Draft
> **Created**: 20260707
> **Scope**: 清理 PR 带来的碎碎念 + 布局精简

## 改动清单

### ExamShellView
- loading: "正在同步考试信息..." → "加载中"，删 `.section-copy` 解释
- gate-card: 删掉整个"系统正在做什么"侧栏 (`.gate-side-card`)
- gate 指引 `<ul>`: 保留前 3 条（时长/题量/保存/风控），删"如果网络中断…" 和 "切屏…会被记录…" 长解释
- pill 标签: "Candidate Session" / "Candidate Access" / "Submitted" → "考试" / "开始" / "已交卷"
- gate-card intro: "开始前先看清考试时长…再输入验证码进入答题" → 删掉

### ExamQuestionPanel
- 删掉 `helperCopy` computed 和 `<p class="question-hint">` — 不需要解释选项怎么点
- 删掉 `question-status-bar`（"当前状态 / 自动保存"）— 不需要实时告诉用户保存状态

### PaperEditorView
- loading fallback: 删 `.section-copy` "编辑器会优先读取后端…"
- pill: "Paper Publish" → "考卷"

### AdminDashboardView / AdminWorkbenchView / CandidateListView / ResultListView
- loading 文案统一: "正在同步xxx..." → "加载中"

### TaskDetailView
- upload tip: "支持多个 PDF，上传后系统会自动解析并创建候选人。" → "支持多个 PDF"

### Placeholder 路由
- ExamStartView / ExamSessionView / ExamSubmittedView: 这三个 placeholder 路由其实已被 ExamShellView 内部 state 替代，路由里改为 redirect 到 `/exam/:token`

## Task Breakdown
- [ ] ExamShellView 精简
- [ ] ExamQuestionPanel 删 helperCopy + status bar
- [ ] PaperEditorView + admin loading 文案
- [ ] TaskDetailView 上传提示
- [ ] Placeholder 路由清理
- [ ] Build 验证
