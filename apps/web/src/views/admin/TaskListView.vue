<template>
  <section class="task-list-page">
    <header class="task-list-page__header">
      <div class="task-list-page__heading" aria-hidden="true">
        <p class="task-list-page__eyebrow">任务中心</p>
        <h2 class="task-list-page__title">筛选任务列表</h2>
        <span class="task-list-page__count">{{ filteredTasks.length }} 条任务</span>
      </div>

      <div class="task-list-page__actions">
        <RouterLink v-slot="{ navigate }" :to="{ name: 'admin-task-create' }" custom>
          <el-button class="task-list-page__create" type="primary" @click="navigate">+ 新建任务</el-button>
        </RouterLink>
      </div>

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
    </header>

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
        :data="pagedTasks"
        row-key="id"
        empty-text="暂无任务"
        class="task-list-table"
        header-row-class-name="task-list-table__header"
        :max-height="tableMaxHeight"
      >
        <el-table-column label="任务名称" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <RouterLink class="task-cell__link" :to="{ name: 'admin-task-detail', params: { taskId: row.id } }">
              <div class="task-cell">
                <strong class="task-cell__title">{{ row.title }}</strong>
              </div>
            </RouterLink>
          </template>
        </el-table-column>

        <el-table-column label="岗位" min-width="180" prop="role" show-overflow-tooltip />

        <el-table-column label="负责人" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="owner-cell">
              <span class="owner-cell__label">{{ buildOwnerLabel(row) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" min-width="170" show-overflow-tooltip>
          <template #default="{ row }">
            {{ formatDateTime(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column label="候选人数" width="110" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.candidateCount }} 人
          </template>
        </el-table-column>

        <el-table-column label="进度" min-width="180" show-overflow-tooltip>
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
            <span class="task-status" :class="`task-status--${statusClassMap[row.status] ?? 'default'}`">
              {{ row.status }}
            </span>
          </template>
        </el-table-column>

        <el-table-column fixed="right" label="操作" width="112">
          <template #default="{ row }">
            <RouterLink v-slot="{ navigate }" :to="{ name: 'admin-task-detail', params: { taskId: row.id } }" custom>
              <button class="task-list-page__action" type="button" @click="navigate">查看详情</button>
            </RouterLink>
          </template>
        </el-table-column>
      </el-table>

      <footer v-if="filteredTasks.length > 0" class="task-list-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="filteredTasks.length"
          layout="total, prev, pager, next"
        />
      </footer>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink } from "vue-router";

import { loadTasks, type ScreeningTaskSummary } from "../../lib/gateway";

const loading = ref(true);
const loadError = ref("");
const keyword = ref("");
const roleFilter = ref("");
const statusFilter = ref("");
const tasks = ref<ScreeningTaskSummary[]>([]);
const currentPage = ref(1);
const pageSize = 10;
const tableMaxHeight = "100%";

const ownerPool = ["华北组", "华东组", "华南组", "中台组", "专项组"];

const statusClassMap: Record<string, string> = {
  待上传: "warning",
  进行中: "processing",
  已暂停: "muted",
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

const totalPages = computed(() => Math.max(1, Math.ceil(filteredTasks.value.length / pageSize)));

const pagedTasks = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return filteredTasks.value.slice(start, start + pageSize);
});

watch([keyword, roleFilter, statusFilter], () => {
  currentPage.value = 1;
});

watch(totalPages, (nextTotalPages) => {
  if (currentPage.value > nextTotalPages) {
    currentPage.value = nextTotalPages;
  }
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
  width: 100%;
  height: calc(100vh - 96px);
  min-height: 0;
  min-width: 0;
  overflow: hidden;
  padding: 14px 16px 16px;
  border-radius: 8px;
  background: #fff;
}

.task-list-page__header {
  display: flex;
  align-items: center;
  flex: none;
  gap: 12px;
  padding: 0 0 4px;
  min-width: 0;
}

.task-list-page__heading {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
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
  flex: none;
  padding-right: 8px;
}

.task-list-page__summary {
  color: #667991;
  font-size: 12px;
}

.task-list-page__filters {
  display: grid;
  grid-template-columns: minmax(140px, 180px) minmax(120px, 160px) minmax(200px, 1fr);
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.task-list-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
  padding: 0;
  background: #ffffff;
}

.task-list-panel__error {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: flex-start;
}

:deep(.task-list-table) {
  --el-table-border-color: #edf1f6;
  --el-table-header-bg-color: #f4f6f9;
  --el-table-row-hover-bg-color: #f7faff;
  --el-table-header-text-color: #526885;
  --el-table-text-color: #1f2f46;
  --el-fill-color-lighter: #f7f9fc;
  flex: 1;
  min-height: 0;
  min-width: 0;
  border: 0;
  border-radius: 0;
}

:deep(.task-list-table .el-table__inner-wrapper),
:deep(.task-list-table .el-table__body-wrapper),
:deep(.task-list-table .el-scrollbar) {
  min-width: 0;
}

:deep(.task-list-table::before),
:deep(.task-list-table__inner-wrapper::before) {
  display: none;
}

:deep(.task-list-table th.el-table__cell) {
  padding: 12px 0;
  background: #f4f6f9;
  color: #394b63;
  font-size: 12px;
  font-weight: 800;
}

:deep(.task-list-table td.el-table__cell) {
  padding: 13px 0;
  border-bottom-color: #edf1f6;
}

.task-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.task-cell__link {
  display: block;
  min-width: 0;
  text-decoration: none;
}

.task-cell__title {
  display: block;
  min-width: 0;
  overflow: hidden;
  color: #153c79;
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  transition: color 0.18s ease;
  white-space: nowrap;
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
  min-width: 0;
}

.owner-cell__label {
  display: block;
  min-width: 0;
  overflow: hidden;
  color: #284b84;
  font-size: 13px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-cell {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
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
  height: 28px;
  padding: 0 10px;
  border: 1px solid #cfe0f8;
  border-radius: 4px;
  background: #f4f8ff;
  color: #2568d8;
  cursor: pointer;
  font-size: 12px;
  font-weight: 700;
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
  border-radius: 4px;
  box-shadow: inset 0 0 0 1px #d7e2ef;
}

:deep(.el-progress-bar__outer) {
  background-color: #e7eef8;
}

:deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #5d8ef0 0%, #2f69d9 100%);
}

.task-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
}

.task-status--warning {
  background: #fff7e8;
  color: #b7791f;
}

.task-status--processing {
  background: #eaf2ff;
  color: #2568d8;
}

.task-status--muted {
  background: #f1f4f8;
  color: #6b7788;
}

.task-status--success {
  background: #eaf8f1;
  color: #23845d;
}

.task-status--danger {
  background: #fff0f0;
  color: #c24141;
}

.task-status--default {
  background: #f1f4f8;
  color: #65758b;
}

.task-list-pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex: none;
  min-height: 46px;
  padding: 10px 4px 0;
}

.task-list-pagination :deep(.el-pagination) {
  --el-pagination-bg-color: #ffffff;
  --el-pagination-button-color: #40546f;
  --el-pagination-hover-color: #2568d8;
  --el-pagination-button-disabled-bg-color: #ffffff;
  font-weight: 600;
}

@media (max-width: 960px) {
  .task-list-page {
    height: auto;
    max-height: none;
    min-height: calc(100vh - 88px);
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
