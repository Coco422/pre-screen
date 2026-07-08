# Product Spec: Pre-Screen

> **Status**: Active
> **Last Updated**: 2026-07-07
> **Owner**: Ray

## Product Outcome

技术岗招聘智能初筛平台。面向非技术背景 HR，借助本地多模态 AI 完成简历理解、候选人画像构建、自动出题、在线考试和编码能力验证的全流程闭环。

## 核心出发点

- 简历量大，一个人来不及筛选
- HR 无技术基础，难以判断一两页技术简历的真实水平
- 应届生简历普遍存在包装，需要带着"质疑"眼光验证

## 核心能力

1. **多模态简历解析**：PDF 上传 → 页面渲染 → Qwen 多模态模型识图 + 文本理解 → 结构化候选人画像
2. **AI 辅助出题**：基于候选人简历和岗位 JD，自动生成针对性考卷（客观题 + 主观题 + 代码题）
3. **在线考试平台**：候选人通过链接+验证码进入考试，支持倒计时、自动保存、心跳、风控事件记录
4. **代码判题**：接 Judge0 在线编译执行，支持多语言试跑和正式提交
5. **结果评分**：客观题自动评分、主观题 AI 辅助评分建议、代码题用例判定

## AI 基础设施

- 模型：Qwen 3.6-27B（多模态，支持识图）
- 部署：本地 http://172.16.99.204:3398（OpenAI 兼容 API）
- 无成本约束

## Success Criteria

- HR 上传简历后，系统自动完成解析 + 出题 + 发卷，无需人工干预技术判断
- 候选人收到链接后可独立完成考试
- HR 可直接看到评分结果和风险提示

## Constraints

- Technical: 本地部署模型，无外部 API 依赖
- Compliance: 简历数据不离开本地环境
- Delivery: 以功能闭环为优先，UI 精简工具型

## 页面结构

| 路由 | 功能 |
|------|------|
| `/login` | HR 登录 |
| `/admin/dashboard` | 工作台（指标 + 待处理列表） |
| `/admin/tasks` | 筛选任务中心 |
| `/admin/tasks/new` | 新建筛选任务 |
| `/admin/tasks/:id` | 任务详情（上传简历 → 解析 → 生成考卷 → 发卷） |
| `/admin/candidates` | 候选人池 |
| `/admin/candidates/:id` | 候选人详情（画像 + PDF 原件 + 操作） |
| `/admin/candidates/:id/edit` | 编辑画像 |
| `/admin/papers/:id` | 考卷编辑 |
| `/admin/results` | 结果中心 |
| `/admin/results/:id` | 结果详情 |
| `/exam/:token/start` | 考试入口 |
| `/exam/:token/session` | 在线作答 |
| `/exam/:token/submitted` | 提交完成 |

## Open Questions

- 主观题 AI 评分是否需要 HR 二次确认
- 是否需要批量对比多个候选人的结果
