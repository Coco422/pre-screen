# 03. 任务中心

- 路由：`/admin/tasks`
- 页面目标：管理岗位筛选任务，快速进入具体任务。

## 接口清单

| Method | Path | 状态 | 用途 |
| --- | --- | --- | --- |
| `GET` | `/api/admin/tasks` | 已有 | 任务列表 |
| `POST` | `/api/admin/tasks` | 已有 | 新建任务 |

## 列表页需要的筛选能力

- `GET /api/admin/tasks?page=1&page_size=20&keyword=&status=&owner_id=&created_from=&created_to=`
- 当前已有接口只有 `status` 和 `keyword`，建议扩展分页和负责人筛选。

## 列表关键字段

- `task_id`
- `title`
- `role/department`
- `owner_name`
- `created_at`
- `candidate_count`
- `progress`
- `status`

## 页面规则

- 表格主入口点击后进入 `/admin/tasks/:taskId`。
- “新建任务”按钮跳转 `/admin/tasks/new`。
- 如果后续负责人是从组织用户体系里选择，还需要补一个用户选择接口，但不属于这个页面的首要阻塞项。
