<template>
  <section class="task-list-page">
    <header class="task-list-page__header">
      <div class="task-list-page__heading">
        <p class="task-list-page__eyebrow">任务中心</p>
        <div class="task-list-page__title-row">
          <h2 class="task-list-page__title">筛选任务列表</h2>
          <span class="task-list-page__count">{{ filteredTasks.length }} 条任务</span>
        </div>
      </div>

      <div class="task-list-page__actions">
        <span class="task-list-page__summary">{{ tasks.length }} 个任务</span>

        <RouterLink v-slot="{ navigate }" :to="{ name: 'admin-task-create' }" custom>
          <el-button class="task-list-page__create" type="primary" @click="navigate">+ 新建任务</el-button>
        </RouterLink>
      </div>
    </header>

    <section class="task-list-page__toolbar">
      <div class="task-list-page__toolbar-card">
        <div class="task-list-page__filters">
          <el-select v-model="roleFilter" clearable placeholder="全部岗位">
            <el-option label="全部岗位" value="" />
            <el-option v-for="role in roleOptions" :key="role" :label="role" :value="role" />
          </el-select>

          <el-select v-model="statusFilter" clearable placeholder="全部状态">
            <el-option label="全部状态" value="" />
            <el-option v-for="status in statusOptions" :key="status" :label="status" :value="status" />
          </el-select>

          <el-input v-model="keyword" clearable placeholder="搜索任务名称 / 岗位 / ID" />
        </div>
      </div>
    </section>

    <section class="task-list-panel">
      <el-skeleton v-if="loading" :rows="6" animated />

      <div v-else-if="loadError" class="task-list-panel__error">
        <el-alert title="任务列表加载失败" :description="loadError" type="error" :closable="false" />
        <el-button size="small" plain @click="void fetchTasks()">重新加载</el-button>
      </div>

      <el-empty
        v-else-if="filteredTasks.length === 0"
        :description="tasks.length === 0 ? '暂无任务' : '没有符合筛选条件的任务'"
      />

      <el-table
        v-else
        :data="filteredTasks"
        row-key="id"
        empty-text="暂无任务"
        class="task-list-table"
        header-row-class-name="task-list-table__header"
      >
        <el-table-column label="任务名称" min-width="280">
          <template #default="{ row }">
            <RouterLink class="task-cell__link" :to="{ name: 'admin-task-detail', params: { taskId: row.id } }">
              <div class="task-cell">
                <strong class="task-cell__title">{{ row.title }}</strong>
                <span class="task-cell__meta">ID {{ row.id }}</span>
              </div>
            </RouterLink>
          </template>
        </el-table-column>

        <el-table-column label="岗位" min-width="180" prop="role" />

        <el-table-column label="负责人" min-width="150">
          <template #default="{ row }">
            <div class="owner-cell">
              <span class="owner-cell__label">{{ buildOwnerLabel(row) }}</span>
              <span class="owner-cell__meta">系统分配</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" min-width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column label="候选人数" width="110">
          <template #default="{ row }">
            {{ row.candidateCount }} 人
          </template>
        </el-table-column>

        <el-table-column label="进度" min-width="180">
          <template #default="{ row }">
            <div class="progress-cell">
              <div class="progress-cell__head">
                <strong>{{ buildProgress(row).percentage }}%</strong>
                <span>{{ buildProgress(row).ratio }}</span>
              </div>
              <el-progress
                :percentage="buildProgress(row).percentage"
                :show-text="false"
                :stroke-width="6"
                :status="buildProgress(row).tone"
              />
            </div>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusToneMap[row.status] ?? 'info'" effect="plain">{{ row.status }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column fixed="right" label="操作" width="96">
          <template #default="{ row }">
            <RouterLink v-slot="{ navigate }" :to="{ name: 'admin-task-detail', params: { taskId: row.id } }" custom>
              <el-button class="task-list-page__action" link type="primary" @click="navigate">进入</el-button>
            </RouterLink>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { loadTasks, type ScreeningTaskSummary } from "../../lib/gateway";

const loading = ref(true);
const loadError = ref("");
const keyword = ref("");
const roleFilter = ref("");
const statusFilter = ref("");
const tasks = ref<ScreeningTaskSummary[]>([]);

const ownerPool = ["华北组", "华东组", "华南组", "中台组", "专项组"];

const statusToneMap: Record<string, "success" | "warning" | "primary" | "info" | "danger"> = {
  待上传: "warning",
  进行中: "primary",
  已暂停: "info",
  已完成: "success",
  已关闭: "danger"
};

const roleOptions = computed(() => Array.from(new Set(tasks.value.map((task) => task.role))).filter(Boolean));
const statusOptions = computed(() => Array.from(new Set(tasks.value.map((task) => task.status))).filter(Boolean));

const filteredTasks = computed(() => {
  const search = keyword.value.trim().toLowerCase();

  return tasks.value.filter((task) => {
    const matchesRole = !roleFilter.value || task.role === roleFilter.value;
    const matchesStatus = !statusFilter.value || task.status === statusFilter.value;
    const matchesKeyword = !search || [task.title, task.role, task.id].join(" ").toLowerCase().includes(search);

    return matchesRole && matchesStatus && matchesKeyword;
  });
});

function hashText(input: string) {
  let hash = 0;

  for (let index = 0; index < input.length; index += 1) {
    hash = (hash * 31 + input.charCodeAt(index)) >>> 0;
  }

  return hash;
}

function buildOwnerLabel(task: ScreeningTaskSummary) {
  const bucket = ownerPool[hashText(`${task.id}:${task.title}:${task.role}`) % ownerPool.length];
  return `系统分配 · ${bucket}`;
}

function buildProgress(task: ScreeningTaskSummary) {
  if (task.uploadCount <= 0) {
    return {
      percentage: 0,
      ratio: task.status === "已完成" ? "已完成" : "待上传",
      tone: task.status === "已完成" ? ("success" as const) : undefined
    };
  }

  const percentage = Math.min(100, Math.round((task.candidateCount / task.uploadCount) * 100));

  return {
    percentage,
    ratio: `${task.candidateCount}/${task.uploadCount}`,
    tone: task.status === "已完成" || percentage >= 100 ? ("success" as const) : undefined
  };
}

function formatDateTime(input: string) {
  const date = new Date(input);
  if (Number.isNaN(date.getTime())) {
    return input;
  }

  const parts = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).formatToParts(date);

  const getPart = (type: string) => parts.find((part) => part.type === type)?.value ?? "";

  return `${getPart("year")}-${getPart("month")}-${getPart("day")} ${getPart("hour")}:${getPart("minute")}`;
}

async function fetchTasks() {
  loading.value = true;

  try {
    tasks.value = await loadTasks();
    loadError.value = "";
  } catch {
    tasks.value = [];
    loadError.value = "请稍后重试。";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void fetchTasks();
});
</script>

<style scoped>
.task-list-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100%;
  padding: 16px 18px 18px;
  border: 1px solid #d6e1ef;
  border-radius: 14px;
  background:
    linear-gradient(180deg, #f7fbff 0%, #f3f7fd 100%),
    #f7fbff;
}

.task-list-page__header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  padding: 4px 4px 8px;
}

.task-list-page__heading {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-list-page__title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.task-list-page__eyebrow {
  margin: 0;
  color: #5b74a2;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.task-list-page__title {
  margin: 0;
  color: #17253d;
  font-size: 20px;
  font-weight: 700;
}

.task-list-page__count {
  display: inline-flex;
  align-items: center;
  height: 22px;
  padding: 0 8px;
  border: 1px solid #d7e3f3;
  border-radius: 999px;
  background: #ffffff;
  color: #496388;
  font-size: 12px;
}

.task-list-page__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-list-page__summary {
  color: #667991;
  font-size: 12px;
}

.task-list-page__toolbar {
  padding: 0;
}

.task-list-page__toolbar-card {
  padding: 10px 12px;
  border: 1px solid #dce6f2;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8px 24px rgba(36, 61, 94, 0.05);
}

.task-list-page__filters {
  display: grid;
  grid-template-columns: 180px 160px minmax(260px, 1fr);
  gap: 10px;
}

.task-list-panel {
  min-height: 360px;
  padding: 10px;
  border: 1px solid #d6e1ef;
  border-radius: 12px;
  background: #ffffff;
}

.task-list-panel__error {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}

:deep(.task-list-table) {
  --el-table-border-color: #dbe4f0;
  --el-table-header-bg-color: #f5f8fc;
  --el-table-row-hover-bg-color: #f8fbff;
  --el-table-header-text-color: #526885;
  --el-table-text-color: #1f2f46;
  --el-fill-color-lighter: #f7fbff;
  border: 1px solid #dbe4f0;
  border-radius: 10px;
}

:deep(.task-list-table th.el-table__cell) {
  padding: 10px 0;
  font-size: 12px;
  font-weight: 700;
}

:deep(.task-list-table td.el-table__cell) {
  padding: 11px 0;
}

.task-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-cell__link {
  display: block;
  text-decoration: none;
}

.task-cell__title {
  color: #153c79;
  font-size: 14px;
  font-weight: 600;
  transition: color 0.18s ease;
}

.task-cell__meta,
.owner-cell__meta {
  color: #7387a1;
  font-size: 12px;
}

.task-cell__link:hover .task-cell__title {
  color: #0f57d3;
}

.owner-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.owner-cell__label {
  color: #284b84;
  font-size: 13px;
  font-weight: 600;
}

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: #54667f;
  font-size: 12px;
}

.progress-cell__head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
}

.progress-cell strong {
  color: #1f4e97;
  font-size: 14px;
}

.task-list-page__action {
  padding: 0;
  font-weight: 600;
}

:deep(.el-button--primary) {
  border-color: #2e63c6;
  background: linear-gradient(180deg, #3a73e0 0%, #2f69d9 100%);
  box-shadow: none;
}

:deep(.el-select),
:deep(.el-input) {
  width: 100%;
}

:deep(.el-input__wrapper),
:deep(.el-select__wrapper) {
  min-height: 36px;
  border-radius: 8px;
  box-shadow: inset 0 0 0 1px #d7e2ef;
}

:deep(.el-progress-bar__outer) {
  background-color: #e7eef8;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #5d8ef0 0%, #2f69d9 100%);
}

@media (max-width: 960px) {
  .task-list-page {
    padding: 16px;
  }

  .task-list-page__header {
    flex-direction: column;
    align-items: stretch;
  }

  .task-list-page__actions {
    justify-content: space-between;
  }

  .task-list-page__filters {
    grid-template-columns: 1fr;
  }
}
</style>
