<template>
  <section class="candidate-page">
    <div class="candidate-page__head">
      <h2 class="section-title">候选人列表</h2>
    </div>

    <div class="candidate-page__filters">
      <el-select v-model="roleFilter" clearable placeholder="全部岗位">
        <el-option label="全部岗位" value="" />
        <el-option v-for="role in roleOptions" :key="role" :label="role" :value="role" />
      </el-select>

      <el-select v-model="statusFilter" clearable placeholder="全部状态">
        <el-option label="全部状态" value="" />
        <el-option label="待审核" value="待审核" />
        <el-option label="待发卷" value="待发卷" />
        <el-option label="待开考" value="待开考" />
        <el-option label="已开考" value="已开考" />
        <el-option label="已交卷" value="已交卷" />
        <el-option label="已完成筛选" value="已完成筛选" />
      </el-select>

      <el-select v-model="pendingReviewFilter" clearable placeholder="全部审核">
        <el-option label="全部审核" value="" />
        <el-option label="待审核" value="true" />
        <el-option label="非待审核" value="false" />
      </el-select>

      <el-select v-model="paperSentFilter" clearable placeholder="全部发卷">
        <el-option label="全部发卷" value="" />
        <el-option label="已发卷" value="true" />
        <el-option label="未发卷" value="false" />
      </el-select>

      <el-input v-model="keyword" clearable placeholder="搜索候选人 / 岗位 / 城市" />
    </div>

    <div v-if="loading" class="candidate-page__state">正在同步候选人列表...</div>
    <div v-else-if="loadError" class="candidate-page__state candidate-page__state--error">{{ loadError }}</div>

    <el-table v-else :data="candidates" class="candidate-page__table" empty-text="没有符合筛选条件的候选人。" row-key="id" stripe>
      <el-table-column label="姓名" prop="name" />
      <el-table-column label="岗位" prop="role" />
      <el-table-column label="PDF 上传时间" min-width="150">
        <template #default="{ row }">
          {{ formatDateTime(row.resumeUploadedAt) }}
        </template>
      </el-table-column>
      <el-table-column label="解析状态" min-width="110">
        <template #default="{ row }">
          {{ parseStatusLabel(row.resumeParseStatus) }}
        </template>
      </el-table-column>
      <el-table-column label="筛选状态" min-width="120">
        <template #default="{ row }">
          <el-tag :type="statusTypeMap[row.screeningStatus] ?? 'info'">{{ row.screeningStatus }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="风险标记" min-width="110">
        <template #default="{ row }">
          <el-tag :type="riskTypeMap[row.riskLevel] ?? 'info'">{{ row.riskFlag }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="更新时间" min-width="150">
        <template #default="{ row }">
          {{ formatDateTime(row.updatedAt) }}
        </template>
      </el-table-column>
      <el-table-column label="下一步" width="120">
        <template #default="{ row }">
          <RouterLink class="candidate-page__action" :to="row.nextAction.target">{{ row.nextAction.label }}</RouterLink>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { loadCandidates, type CandidateCard, type CandidateListFilters } from "../../lib/gateway";

const route = useRoute();
const loading = ref(true);
const loadError = ref("");
const keyword = ref("");
const roleFilter = ref("");
const statusFilter = ref("");
const pendingReviewFilter = ref("");
const paperSentFilter = ref("");
const candidates = ref<CandidateCard[]>([]);
let latestRequestId = 0;

const statusTypeMap: Record<string, "success" | "warning" | "primary" | "info" | "danger"> = {
  待审核: "warning",
  待发卷: "primary",
  待开考: "info",
  已开考: "danger",
  已交卷: "success",
  已完成筛选: "success"
};

const riskTypeMap: Record<string, "success" | "warning" | "primary" | "info" | "danger"> = {
  low: "info",
  medium: "warning",
  high: "danger"
};

const roleOptions = computed(() => Array.from(new Set(candidates.value.map((candidate) => candidate.role))).filter(Boolean));

const currentTaskId = computed(() => readQueryString("taskId") || readQueryString("task_id"));

function readQueryString(key: string) {
  const value = route.query[key];
  return typeof value === "string" ? value : "";
}

function parseBooleanFilter(value: string): boolean | undefined {
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  return undefined;
}

function syncFiltersFromRoute() {
  roleFilter.value = readQueryString("role");
  statusFilter.value = readQueryString("status");
  pendingReviewFilter.value = readQueryString("pendingReview") || readQueryString("pending_review");
  paperSentFilter.value = readQueryString("paperSent") || readQueryString("paper_sent");
  keyword.value = readQueryString("keyword");
}

function buildFilters(): CandidateListFilters {
  return {
    taskId: currentTaskId.value || undefined,
    role: roleFilter.value || undefined,
    status: statusFilter.value || undefined,
    pendingReview: parseBooleanFilter(pendingReviewFilter.value),
    paperSent: parseBooleanFilter(paperSentFilter.value),
    keyword: keyword.value.trim() || undefined,
    sortBy: statusFilter.value === "已交卷" ? "updated_at" : "resume_uploaded_at",
    order: statusFilter.value === "已交卷" ? "desc" : "asc"
  };
}

function formatDateTime(value?: string | null) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  const parts = new Intl.DateTimeFormat("zh-CN", {
    timeZone: "Asia/Shanghai",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).formatToParts(date);

  const getPart = (type: string) => parts.find((part) => part.type === type)?.value ?? "";
  return `${getPart("month")}-${getPart("day")} ${getPart("hour")}:${getPart("minute")}`;
}

function parseStatusLabel(status: string) {
  const labels: Record<string, string> = {
    queued: "排队中",
    parsing: "解析中",
    parsed: "已解析",
    failed: "解析失败",
    missing: "未上传"
  };
  return labels[status] ?? status;
}

async function loadCandidateList() {
  const requestId = ++latestRequestId;
  loading.value = true;

  try {
    const nextCandidates = await loadCandidates(buildFilters());
    if (requestId !== latestRequestId) {
      return;
    }

    candidates.value = nextCandidates;
    loadError.value = "";
  } catch {
    if (requestId !== latestRequestId) {
      return;
    }

    loadError.value = "候选人列表加载失败，等待后端接口恢复。";
    candidates.value = [];
  } finally {
    if (requestId === latestRequestId) {
      loading.value = false;
    }
  }
}

syncFiltersFromRoute();

watch(
  () => route.query,
  () => {
    syncFiltersFromRoute();
  },
  { deep: true }
);

watch(
  [currentTaskId, roleFilter, statusFilter, pendingReviewFilter, paperSentFilter, keyword],
  () => {
    void loadCandidateList();
  },
  { immediate: true }
);
</script>
