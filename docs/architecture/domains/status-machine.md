# Status Machine (frozen for production cutover)

> **Status**: Frozen draft for implementation  
> **Updated**: 2026-07-09  
> **Code mirror**: `pre_screen_common.status`  
> **Plan**: `plans/plan-20260709-production-cutover.md` Phase 0.1

对外 API / UI 继续使用 **中文状态文案**（与现网 demo 一致）。  
库内与代码枚举使用 **稳定英文 code**，序列化时映射为中文 label。

## Candidate screening status

| Code | Label (API/UI) | Meaning |
|------|----------------|---------|
| `resume_uploaded` | 已上传简历 | PDF 已收，未开始解析 |
| `extracting` | 信息提取中 | PyMuPDF / 多模态提取中（兼容旧值：`解析中`） |
| `profiling` | 信息整理中 | LLM 画像整理（兼容：`待审核` 的一部分） |
| `pending_review` | 待审核 | 画像待 HR 确认 |
| `paper_generating` | 拟出卷中 | 正在生成考卷草稿 |
| `ready_to_publish` | 待发卷 | 草稿可发 |
| `paper_sent` | 已发卷 | 链接+验证码已生成（兼容：`待开考`） |
| `exam_in_progress` | 进行中考试 | 候选人已开考（兼容：`已开考`） |
| `submitted` | 已交卷 | 已交卷待评分/复核（兼容：`已完成` 误用场景需纠正） |
| `reviewing` | 评分复核中 | HR 修分中 |
| `screening_passed` | 已完成筛选 | pass |
| `screening_rejected` | 已淘汰 | reject |
| `archived` | 已归档 | 归档 |

### Compatibility aliases (read path)

| Legacy label | Canonical code |
|--------------|----------------|
| `解析中` | `extracting` |
| `待审核` | `pending_review` |
| `待发卷` | `ready_to_publish` |
| `待开考` | `paper_sent` |
| `已开考` | `exam_in_progress` |
| `已完成` | `submitted`（仅当结果上下文；候选人终态应升级） |
| `已交卷` | `submitted` |
| `已完成筛选` | `screening_passed` |
| `已归档` | `archived` |

写入路径应逐步只写 **code**；过渡期 Gateway 可同时接受 label 并规范化。

## Task status

| Code | Label |
|------|-------|
| `open` | open |
| `closed` | closed |

## Upload / parse job status

| Code | Meaning |
|------|---------|
| `queued` | 入队 |
| `running` | 解析中 |
| `parsed` / `succeeded` | 成功 |
| `failed` | 失败 |

Processing stages: `queued` → `pdf_parse` → `project_extract` → `profile_ready` → `paper_generate` → `published`.

## Paper status

| Code | Meaning |
|------|---------|
| `draft` | 草稿 |
| `published` | 已发布 |

## Exam session status

| Code | Meaning |
|------|---------|
| `in_progress` | 作答中 |
| `submitted` | 已交卷 |
| `expired` | 超时结束 |

## Result / review status

| Field | Values |
|-------|--------|
| `result.status` | `submitted`, `reviewed`, `completed` |
| `review_status` | `pending`, `reviewing`, `reviewed` |
| `screening_decision` | `pass`, `reject`, null |

## Dashboard buckets

| Bucket | Candidate codes / labels |
|--------|--------------------------|
| Screening in progress | `extracting`, `profiling`, `pending_review` (+ legacy 解析中/待审核) |
| Pending publish | `ready_to_publish` / 待发卷 |
| Exam in progress | `exam_in_progress` / 已开考/进行中考试 |
| Submitted | `submitted` / 已交卷 |
| Screening completed | `screening_passed`, `archived` / 已完成筛选/已归档 |
