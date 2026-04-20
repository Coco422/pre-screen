# 招聘预筛考卷系统设计文档

## 1. 项目目标

本项目要做的是一个面向技术岗初筛的招聘考卷系统。第一期以内部 HR 使用为主，核心链路是：

1. HR 上传候选人 PDF 简历。
2. 系统解析候选人信息，生成结构化候选人档案。
3. HR 选择岗位模板并粘贴 JD，系统生成一份可审核的考卷草稿。
4. HR 审核和编辑考卷后，生成专属考试链接和验证码并发给候选人。
5. 候选人在线完成基础信息题、客观题、主观题和代码题。
6. 系统完成自动判题、主观题建议评分和风控事件汇总，供 HR 查看。

第一期明确支持技术岗，优先服务前端、后端、全栈等研发岗位。

## 2. 首期范围

### 2.1 In Scope

- HR 后台上传 PDF 简历。
- PDF 解析与候选人结构化档案生成。
- 岗位模板管理与模板复制后二次编辑。
- `模板为主 + JD/简历微调` 的考卷生成模式。
- 题型支持：
  - 基础信息题
  - 客观题
  - 主观题
  - 代码题
- 候选人通过专属链接 + 一次性验证码进入考试。
- 一次性连续开考、限时作答、不可重考。
- 自动保存：
  - 前端防抖保存
  - 后端草稿落库
  - 本地缓存兜底
- 自动判题：
  - 客观题自动评分
  - 代码题 Judge0 自动判题
  - 主观题 LLM 建议评分，HR 最终确认
- 轻量风控留痕：
  - 切页
  - 失焦
  - 复制/粘贴
  - 网络断连/恢复
  - 心跳异常
- 开发与部署约束：
  - 后端优先使用 FastAPI
  - 前端优先使用 Vue
  - 项目依赖使用 `uv`
  - 部署使用 Docker
  - 数据库使用 PostgreSQL
  - 迁移使用 Flyway
  - 文件对象存储使用 MinIO
  - 开发流采用 `main + feature branch + PR`

### 2.2 Out of Scope

- AI 辅助初面
- 远程监考能力，如摄像头、麦克风、录屏
- 复杂反作弊策略，如代码相似度检测、自动判作弊
- 交互题、特判题、文件 IO 题
- 多租户完整产品化能力
- 自定义代码运行镜像和复杂编译环境

## 3. 关键产品决策

### 3.1 产品定位

- 产品本质是招聘考卷系统，不是通用问卷系统。
- 个人信息采集是考卷的一部分，不是独立流程。
- 第一阶段聚焦技术岗。

### 3.2 出卷模式

- 采用 `模板为主 + 简历/JD 微调`。
- 岗位模板决定题型比例、必出题、难度边界和禁区。
- LLM 负责候选人画像归纳、题目候选集筛选和一部分个性化追问。
- 首期代码题来自题库，不采用全动态即时生成。

### 3.3 考试入口

- 候选人通过专属链接 + 一次性验证码进入考试。
- 验证码由后台生成，HR 自行通过外部渠道发送。
- 首期不接手机号、邮箱验证码，也不做候选人注册账号。

### 3.4 审核机制

- 系统生成的考卷草稿必须由 HR 审核后才能发出。
- HR 可以改题、删题、调分值、调整文字表述。

### 3.5 评分策略

- 客观题自动判分。
- 代码题自动判分。
- 主观题由 LLM 给出建议分和评分理由，HR 最终确认。

## 4. 架构设计

首期采用“前期拆服务，但控制粒度”的架构，而不是模块化单体，也不是过度微服务。

### 4.1 服务划分

#### 1. API Gateway / BFF

职责：

- 统一前端入口
- 后台管理员鉴权
- 候选人考试入口校验
- 接口聚合
- 基础限流

#### 2. Resume Service

职责：

- PDF 上传
- MinIO 文件写入
- PDF 文本提取
- 图片页渲染
- 多模态兜底解析
- 候选人档案结构化

#### 3. Exam Service

职责：

- 岗位模板管理
- 题库管理
- 考卷生成
- 考卷草稿审核
- 邀请链接和验证码管理
- 考试会话管理
- 答卷草稿保存

#### 4. Judge Bridge Service

职责：

- 封装 Judge0 接口
- 语言与题目配置映射
- 运行与正式提交分流
- 提交轮询
- 结果归档

#### 5. Scoring Service

职责：

- 客观题评分
- 主观题建议分生成
- 代码题得分汇总
- 整卷总分汇总
- HR 最终评分确认

#### 6. Risk Event Service

职责：

- 风控事件接收
- 心跳日志接收
- 网络异常记录
- 考试审计日志归档

### 4.2 基础设施

- PostgreSQL：主业务数据库
- Flyway：迁移管理
- Redis：缓存、会话辅助、异步协同
- Celery：异步任务执行
- MinIO：PDF、页面截图、中间 JSON 等对象存储
- Judge0：代码运行沙箱
- 外部 LLM API：候选人档案提取、考卷生成、主观题建议评分

### 4.3 部署拓扑

- 候选人端和 HR 后台通过公网访问 Gateway。
- 核心后端服务和 Judge0 放在内网。
- Gateway/反向代理做公网入口控制。
- Judge0 不直接暴露给公网。

## 5. 开发与交付规范

### 5.1 技术栈

- 后端：FastAPI
- 前端：Vue
- Python 依赖管理：`uv`
- 容器化：Docker
- 数据库：PostgreSQL
- 数据库迁移：Flyway
- 对象存储：MinIO
- 异步任务：Celery

### 5.2 Git Workflow

采用轻量开发流：

- 长期分支：`main`
- 日常开发：`feature/*`
- 合并方式：PR + Review
- 合并策略：建议 Squash Merge
- 提交规范：建议 Conventional Commits
- `main` 保护分支：开启

不采用经典 `main + develop + release/hotfix` 的 Git Flow。

原因：

- 首期由少数人开发，更适合短生命周期功能分支。
- 降低流程负担，提升迭代速度。
- 仍然保留代码审查和发布规范。

## 6. 数据模型设计

### 6.1 总体原则

- 一套 PostgreSQL 实例。
- 按服务维度划分 schema，而不是一开始就拆成多库。
- 每个服务使用自己的 Flyway migration 管理所属表。
- 大多数核心业务表预留 `org_id` 字段，为未来多租户演进做准备。
- PDF 原件、页面截图和大对象内容放 MinIO，不写入 PostgreSQL 二进制字段。

### 6.2 推荐 schema

- `auth`
- `resume`
- `exam`
- `judge`
- `scoring`
- `risk`

### 6.3 核心实体

#### `resume.candidates`

候选人主档。

关键字段建议：

- `id`
- `org_id`
- `name`
- `phone`
- `email`
- `status`
- `created_at`
- `updated_at`

#### `resume.resume_files`

简历文件元数据。

关键字段建议：

- `candidate_id`
- `minio_bucket`
- `minio_object_key`
- `file_name`
- `file_size`
- `page_count`
- `parse_status`
- `parse_error`

#### `resume.resume_pages`

按页记录提取状态。

关键字段建议：

- `resume_file_id`
- `page_number`
- `text_char_count`
- `rendered_image_key`
- `needs_multimodal`
- `extract_source`
- `extract_confidence`

#### `resume.candidate_profiles`

结构化候选人档案。

关键字段建议：

- `candidate_id`
- `raw_profile_json`
- `normalized_profile_json`
- `source_summary`
- `review_status`
- `reviewed_by`

#### `exam.job_templates`

岗位模板。

关键字段建议：

- `id`
- `org_id`
- `name`
- `role_type`
- `level`
- `template_config_json`
- `copied_from_template_id`

#### `exam.question_bank_items`

题库题目。

关键字段建议：

- `id`
- `question_type`
- `title`
- `body`
- `difficulty`
- `tags`
- `answer_key_json`
- `scoring_rule_json`

#### `exam.exam_papers`

一份实际发出的考卷快照。

关键字段建议：

- `candidate_id`
- `job_template_id`
- `jd_text`
- `title`
- `paper_snapshot_json`
- `generated_by_model`
- `prompt_version`
- `generation_status`
- `review_status`

说明：

- 发出去的考卷必须快照化。
- 后续模板变更不能影响已发考卷。

#### `exam.exam_questions`

考卷中的具体题目实例。

关键字段建议：

- `exam_paper_id`
- `sort_order`
- `question_type`
- `source_type`
- `content_json`
- `score`
- `is_required`

#### `exam.exam_invitations`

候选人邀请记录。

关键字段建议：

- `exam_paper_id`
- `access_token`
- `one_time_code_hash`
- `expires_at`
- `sent_status`

#### `exam.exam_sessions`

考试会话。

关键字段建议：

- `exam_paper_id`
- `invitation_id`
- `status`
- `start_at`
- `expire_at`
- `submitted_at`
- `last_heartbeat_at`

建议状态：

- `draft`
- `in_progress`
- `submitted`
- `expired`
- `reviewed`

#### `exam.exam_answers`

按题保存答案。

关键字段建议：

- `session_id`
- `exam_question_id`
- `draft_answer_json`
- `final_answer_json`
- `last_saved_at`
- `final_submitted_at`

#### `judge.programming_questions`

代码题定义。

关键字段建议：

- `question_bank_item_id`
- `supported_languages`
- `time_limit_ms`
- `memory_limit_kb`
- `stdin_mode`
- `sample_cases_json`

#### `judge.test_cases`

测试用例。

关键字段建议：

- `programming_question_id`
- `visibility`
- `input_data`
- `expected_output`
- `score_weight`

#### `judge.code_submissions`

候选人每次代码提交。

关键字段建议：

- `session_id`
- `exam_question_id`
- `language`
- `submission_type`
- `source_code`
- `status`
- `score`

说明：

- `submission_type` 必须区分 `run` 和 `submit`。

#### `judge.judge_runs`

Judge0 交互明细。

关键字段建议：

- `code_submission_id`
- `judge0_submission_id`
- `stdout`
- `stderr`
- `compile_output`
- `time_used`
- `memory_used`
- `exit_status`
- `raw_result_json`

#### `scoring.subjective_score_suggestions`

主观题建议分。

关键字段建议：

- `session_id`
- `exam_question_id`
- `model_name`
- `prompt_version`
- `suggested_score`
- `reasoning_summary`
- `raw_result_json`

#### `scoring.manual_reviews`

HR 手工确认结果。

关键字段建议：

- `session_id`
- `exam_question_id`
- `reviewer_id`
- `final_score`
- `comment`

#### `scoring.score_summaries`

整卷结果汇总。

关键字段建议：

- `session_id`
- `objective_score`
- `subjective_score`
- `coding_score`
- `total_score`
- `risk_summary_json`

#### `risk.risk_events`

风控事件主表。

关键字段建议：

- `session_id`
- `event_type`
- `event_time`
- `payload_json`

建议事件类型：

- `blur`
- `focus`
- `visibility_hidden`
- `visibility_visible`
- `copy`
- `paste`
- `network_offline`
- `network_online`
- `heartbeat_timeout`

## 7. PDF 解析与候选人档案生成

### 7.1 总体策略

首期采用 `文本优先 + 图像兜底 + 高质量模式校验`，而不是单一路径。

原因：

- 招聘平台导出的 PDF 经常视觉上像截图式简历，但并不一定是纯扫描件。
- 文本层仍然存在时，PyMuPDF 直接提取更快、更稳、结构化更容易。
- 对于低文本覆盖页、图片页或疑似扫描页，再走图片/多模态补读。
- 由于本项目优先质量而不是成本，允许增加多模态校验步骤。

### 7.2 本地样本验证结论

2026-04-21 对本地 `PDFs/` 目录中的 4 份样本 PDF 做了快速验证。

验证方法：

- 使用 PyMuPDF 读取每页文本字符数和图片对象数。
- 输出首页 PNG 做人工抽查。

结果：

- 4 份样本全部存在可提取文本层。
- 单页字符量大致在 1670 到 2245 之间。
- 说明这类招聘平台导出 PDF 并非默认视为纯扫描件。

结论：

- 不能把“图像 -> Markdown”设为唯一主流程。
- 但应把图像链路做成一等公民，并支持整份简历的高质量多模态校验模式。

### 7.3 推荐流水线

1. HR 上传 PDF 到 MinIO。
2. Resume Service 使用 PyMuPDF 提取页面文本和基础结构。
3. 对每一页计算：
   - 文本字符量
   - 图片对象数
   - 文本覆盖率
4. 识别低质量页或疑似扫描页。
5. 对低质量页渲染为图片并调用多模态模型补读。
6. 将文本提取和多模态补读结果合并成候选人结构化档案。
7. 输出字段置信度、提取来源和错误信息。
8. HR 可以修正候选人档案，也可以直接去生成考卷。

### 7.4 输出字段

至少覆盖：

- 基础信息：
  - 姓名
  - 手机号
  - 邮箱
  - 城市
  - 出生年
- 教育背景：
  - 学校
  - 专业
  - 学历
  - 毕业时间
- 工作/项目背景：
  - 工作年限
  - 目标方向
  - 技术栈
  - 项目经历
  - 亮点
  - 疑点
- 扩展信息：
  - 身高
  - 体重
  - 爱好
  - 其他企业自定义字段

## 8. LLM 接入策略

### 8.1 统一 AI Client

必须封装统一 AI Client，不在业务代码中散落调用。

职责：

- 统一 `base_url`
- 统一模型名
- 统一鉴权
- 统一超时、重试和错误格式
- 统一日志和指标输出

要求：

- API key 仅通过环境变量注入
- 不写入 git
- 不直接硬编码到代码或文档

### 8.2 LLM 使用场景

#### 候选人档案结构化

- 将 PDF 文本和图片信息整合为结构化档案。

#### 考卷草稿生成

输入：

- 岗位模板
- JD 文本
- 候选人结构化档案
- 固定出题规则

输出：

- 一份待审核的考卷草稿

#### 主观题建议评分

输入：

- 题目内容
- 候选人回答
- 评分标准

输出：

- 建议分
- 理由摘要
- 风险/亮点摘要

### 8.3 提示词治理

- 所有 prompt 模板必须版本化。
- 所有结果尽量强制 JSON Schema 输出。
- 存储字段至少包括：
  - `model_name`
  - `prompt_version`
  - `raw_result_json`
  - `latency_ms`
  - `token_usage`
  - `error_code`

## 9. 考卷生成设计

### 9.1 生成模式

首期采用 `模板为主 + 简历/JD 微调`。

### 9.2 固定规则

#### 基础信息题

- 固定字段题
- 可按岗位追加少量扩展题

#### 客观题

- 以模板题库为主
- 建议 70% 使用固定题库题
- 允许 20% 到 30% 做个性化调整

#### 主观题

固定方向建议：

- 项目复盘
- 技术取舍
- 问题定位

#### 代码题

- 首期从题库中选择
- 不做全动态即时生成

### 9.3 HR 审核

系统生成后进入草稿状态，HR 必须审核通过才能发出。

允许 HR：

- 改题
- 删题
- 调整排序
- 调整分值
- 调整表述

## 10. 考试会话与作答体验

### 10.1 会话规则

- 一次性开考
- 限时作答
- 开考后连续进行
- 到时自动交卷
- 不允许重考

### 10.2 自动保存

必须同时具备：

- 前端输入防抖自动保存
- 服务端草稿落库
- 本地缓存兜底

目的：

- 防止断电、断网、浏览器意外关闭导致作答丢失

### 10.3 计时机制

- 以后端记录的 `start_at` 和 `expire_at` 为准
- 前端倒计时只做展示
- 前端定期心跳同步会话状态
- 心跳异常要记录

## 11. Judge0 与代码题设计

### 11.1 首期支持语言

产品首发建议开放：

- C
- C++
- Java
- Python
- JavaScript
- TypeScript
- Go
- Rust

第二批预留语言：

- Kotlin
- C#
- PHP

说明：

- Judge0 官方资料说明其支持 90+ 语言，并区分 CE 与 Extra CE 两种 flavor。
- 因此系统架构层应预留更广语言支持。
- 但产品首发语言应控制在题库和编辑器体验都能覆盖的范围内。

### 11.2 运行模式

候选人对代码题支持两种操作：

- `Run`：试跑样例
- `Submit`：正式提交

要求：

- 样例用例对 `Run` 可见
- 隐藏用例只参与 `Submit`
- 每次试跑和正式提交都单独留档

### 11.3 首期边界

支持：

- 时间限制
- 内存限制
- 输出大小限制
- 每题多语言选择

暂不支持：

- 交互题
- 特判器
- 文件 IO 题
- 自定义运行镜像

### 11.4 判分逻辑

- 客观题：自动判分
- 主观题：LLM 建议评分 + HR 确认
- 代码题：按隐藏测试用例通过率换算得分
- 默认取最后一次正式提交作为该题最终成绩

## 12. 风控与审计

### 12.1 首期记录事件

- `blur/focus`
- `visibilitychange`
- `copy/paste`
- `network_offline/network_online`
- `heartbeat_timeout`

### 12.2 设计原则

- 首期只留痕，不自动判作弊
- 风控结果只作为 HR 参考
- 风控事件必须独立存表
- 风控事件在结果页形成摘要

## 13. 页面与核心流程

### 13.1 HR 后台

关键页面：

- 候选人列表页
- 候选人详情页
- 简历解析结果页
- 岗位模板页
- 考卷编辑页
- 发送邀请页
- 结果查看页

主流程：

1. 新建筛选任务
2. 上传 PDF
3. 系统解析候选人档案
4. 选择岗位模板并粘贴 JD
5. 生成考卷草稿
6. HR 审核和编辑
7. 生成链接和验证码并发送

### 13.2 候选人端

关键页面：

- 链接入口页
- 验证码校验页
- 考前说明页
- 在线考试页
- 交卷完成页

主流程：

1. 通过专属链接进入
2. 输入验证码
3. 阅读考前说明并确认开考
4. 先填写基础信息
5. 继续完成客观题、主观题和代码题
6. 手动交卷或超时自动交卷

## 14. 安全与稳定性要求

- 所有外部服务凭证使用环境变量注入。
- Judge0 仅允许内网访问。
- 候选人答卷写操作接口必须做会话鉴权和限速。
- 代码执行结果要和考试会话绑定，避免越权查询。
- LLM 原始响应要保留摘要和错误信息，便于回溯。
- 自动保存接口必须幂等。
- 交卷接口必须具备重复提交保护。

## 15. 第一阶段实施优先级

### P0

- Git 仓库初始化
- Docker 开发环境骨架
- PostgreSQL + MinIO 本地环境
- Flyway 初始化
- FastAPI 服务骨架
- Vue 项目骨架
- AI Client 最小调用验证
- Judge0 联调最小闭环

### P1

- Resume Service：PDF 上传、MinIO 写入、PyMuPDF 提取、图片兜底
- Exam Service：模板、题库、考卷草稿
- 候选人入场与考试会话
- 自动保存与心跳
- Judge Bridge + 基础代码题判题

### P2

- 主观题建议评分
- 风控事件摘要
- HR 结果页
- 模板复制后二次编辑

## 16. 外部参考

- Judge0 GitHub：<https://github.com/judge0/judge0>
- Judge0 Languages Docs：<https://docs.judge0.com/products/judge0/http_api/languages/>
- PyMuPDF Documentation：<https://pymupdf.readthedocs.io/>
- HackerRank：<https://www.hackerrank.com/>
- Codility：<https://www.codility.com/>
- CoderPad：<https://coderpad.io/>
- TestGorilla：<https://www.testgorilla.com/>

## 17. 当前结论

这份设计的核心取向是：

- 产品上先聚焦“招聘考卷系统”，而不是做宽泛招聘平台。
- 技术上前期拆服务，但控制复杂度。
- 简历处理走 `文本优先 + 图像兜底 + 高质量模式校验`。
- 出卷走 `模板为主 + 简历/JD 微调`。
- 判题走 Judge0，自托管内网部署。
- 主观题评分走人机协同。
- 工程上以 `uv + Docker + Postgres + Flyway + MinIO + Celery` 为底座。

这份设计足够支撑下一步进入实现计划拆解。
