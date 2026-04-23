# 04. 新建筛选任务页

- 路由：`/admin/tasks/new`
- 页面目标：创建岗位筛选任务，为后续上传 PDF 和出卷做准备。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/exam-templates` | 建议新增 | 拉取岗位模板列表 |
| `POST` | `/api/admin/tasks` | 已有 | 创建筛选任务 |

## 页面使用方式

- `GET /api/admin/exam-templates`
  - 用于模板下拉选择
  - 建议返回：`template_id`、`name`、`role_type`、`level`、`template_config`
- `POST /api/admin/tasks`
  - 请求体至少包含：`title`、`department/role`、`jd_text`、`template_id/template_config`、`duration_minutes`
  - 成功后返回 `task_id`

## 页面规则

- 创建成功直接跳转 `/admin/tasks/:taskId`。
- 如果页面允许直接粘贴 JD 并选择模板，前端不需要再额外拆步骤页。
- 当前仓库里底层已有 `/internal/exam/templates`，但 Gateway 还没有暴露给前端，需要补一层 `/api/admin/exam-templates`。
