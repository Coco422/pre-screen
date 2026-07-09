# 19. 考卷列表 + 异步生成考卷（UX 闭环）

> 更新：2026-07-09

## 问题（用户实测）

- 解析完 PDF 后点「发卷」→ 跳进编辑器只显示加载中。
- 根因：无 paper 时跳 `/admin/papers/new` 并在编辑页同步调用生成接口，AI 耗时长，前端无进度。

## 正确产品流

```
上传 PDF →（长任务）解析画像
       → 点「生成考卷」→（长任务）出题组装草稿
       → 点「编辑考卷」→ 人工改题
       → 点「确认发布」→ 链接+验证码 → 候选人考试
```

**「发卷」≠ 生成考卷。** 发卷 = 发布考试入口；生成 = 异步出题任务。

## 前端

| 页面 | 行为 |
|------|------|
| 任务详情候选人行 | 无 paper →「生成考卷」按钮；生成中 → 进度%；有 paper →「编辑考卷」 |
| 候选人详情 | 同上 |
| 考卷编辑器 | 不再在 `paperId=new` 时同步生成；提示回任务页生成 |
| 考卷管理 `/admin/papers` | 列表草稿/已发布，进入编辑器 |

## 后端

| Method | Path | 状态码 | 行为 |
|--------|------|--------|------|
| `POST` | `/api/admin/candidates/:id/papers/generate` | **202** | 入队异步生成；立即返回 `status=generating` + processing |
| `GET` | `/api/admin/papers` | 200 | 列表（status/task_id 筛选） |
| `GET` | `/api/admin/papers/:id` | 200 | 草稿详情（编辑） |
| `POST` | `/api/admin/papers/:id/publish` | 201 | 发布链接+验证码 |

生成中候选人状态：`拟出卷中`；processing.stage=`paper_generate`。  
完成后：`待发卷`，写入 `paper_ids`。

## 数据（生产化）

- 生成 job 可落 `exam.paper_jobs` 或复用 candidate.processing jsonb（当前 demo 内存）。
- 落库后 worker 与 PDF 解析共用 Redis broker。

## 结果中心与淘汰

- **已淘汰仍可查看** 是预期：档案留痕，支持争议回看。
- 列表展示结论徽章（已通过/已淘汰/待复核），支持筛选。
