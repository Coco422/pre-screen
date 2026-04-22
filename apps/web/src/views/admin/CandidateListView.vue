<template>
  <section class="candidate-page page-panel">
    <div class="candidate-page__head">
      <div>
        <h2 class="section-title">候选人列表</h2>
        <p class="section-copy">按岗位、状态和关键字快速筛选候选人。</p>
      </div>
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
        <el-option label="已发卷" value="已发卷" />
        <el-option label="已开考" value="已开考" />
        <el-option label="已完成" value="已完成" />
        <el-option label="已交卷" value="已交卷" />
      </el-select>

      <el-input v-model="keyword" clearable placeholder="搜索候选人 / 岗位 / 城市" />
    </div>

    <div v-if="loading" class="candidate-page__state">正在同步候选人列表...</div>
    <div v-else-if="loadError" class="candidate-page__state candidate-page__state--error">{{ loadError }}</div>

    <el-table v-else :data="filteredCandidates" class="candidate-page__table" empty-text="没有符合筛选条件的候选人。" row-key="id" stripe>
      <el-table-column label="姓名" prop="name" />
      <el-table-column label="岗位" prop="role" />
      <el-table-column label="城市" prop="city" />
      <el-table-column label="解析状态" prop="quality" />
      <el-table-column label="筛选状态" prop="status">
        <template #default="{ row }">
          <el-tag :type="statusTypeMap[row.status] ?? 'info'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="260">
        <template #default="{ row }">
          <div class="candidate-page__actions">
            <RouterLink :to="{ name: 'admin-candidate-detail', params: { candidateId: row.id } }">详情</RouterLink>
            <RouterLink :to="{ name: 'admin-candidate-edit', params: { candidateId: row.id } }">编辑</RouterLink>
            <RouterLink
              :to="{
                name: 'admin-paper-editor',
                params: { paperId: row.paperId ?? 'new' },
                query: { candidateId: row.id, candidateName: row.name }
              }"
            >
              发卷
            </RouterLink>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { loadCandidates, type CandidateCard } from "../../lib/gateway";

const route = useRoute();
const loading = ref(true);
const loadError = ref("");
const keyword = ref("");
const roleFilter = ref("");
const statusFilter = ref("");
const candidates = ref<CandidateCard[]>([]);
let latestRequestId = 0;

const statusTypeMap: Record<string, "success" | "warning" | "primary" | "info" | "danger"> = {
  待审核: "warning",
  待发卷: "primary",
  已发卷: "info",
  已开考: "danger",
  已完成: "success",
  已交卷: "success"
};

const roleOptions = computed(() => Array.from(new Set(candidates.value.map((candidate) => candidate.role))).filter(Boolean));

const filteredCandidates = computed(() => {
  const search = keyword.value.trim().toLowerCase();

  return candidates.value.filter((candidate) => {
    const matchesRole = !roleFilter.value || candidate.role === roleFilter.value;
    const matchesStatus = !statusFilter.value || candidate.status === statusFilter.value;
    const matchesKeyword =
      !search ||
      [candidate.name, candidate.role, candidate.city, candidate.summary, ...candidate.skills]
        .join(" ")
        .toLowerCase()
        .includes(search);

    return matchesRole && matchesStatus && matchesKeyword;
  });
});

async function loadCandidateList(taskId?: string) {
  const requestId = ++latestRequestId;
  loading.value = true;

  try {
    const nextCandidates = await loadCandidates(taskId);
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

watch(
  () => route.query.taskId,
  (taskId) => {
    void loadCandidateList(typeof taskId === "string" ? taskId : undefined);
  },
  { immediate: true }
);

watch(
  () => route.query.status,
  (status) => {
    statusFilter.value = typeof status === "string" ? status : "";
  },
  { immediate: true }
);
</script>
