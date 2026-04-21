<template>
  <section class="glass-card page-card">
    <div class="page-head">
      <div>
        <div class="pill">Candidates</div>
        <h2 class="section-title page-title">候选人列表</h2>
      </div>
      <div class="head-actions">
        <RouterLink class="secondary-btn" :to="{ name: 'admin-workbench' }">返回工作台</RouterLink>
        <RouterLink v-if="nextActionCandidate" class="primary-btn" :to="nextActionCandidate.detailTarget">继续处理</RouterLink>
      </div>
    </div>

    <div class="metric-grid">
      <article class="metric-tile" v-for="metric in metrics" :key="metric.label">
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-label">{{ metric.label }}</div>
      </article>
    </div>

    <div class="toolbar">
      <input v-model="keyword" class="soft-input" placeholder="搜索候选人 / 邮箱 / 岗位" />
      <select v-model="statusFilter" class="soft-select">
        <option value="全部状态">全部状态</option>
        <option value="待审核">待审核</option>
        <option value="待发卷">待发卷</option>
        <option value="已发卷">已发卷</option>
        <option value="已开考">已开考</option>
        <option value="已交卷">已交卷</option>
      </select>
      <button class="secondary-btn" type="button" @click="resetFilters">重置筛选</button>
    </div>

    <div v-if="loading" class="state-card">正在同步候选人列表...</div>
    <div v-else-if="loadError" class="state-card">{{ loadError }}</div>

    <div v-else-if="filteredCandidates.length" class="candidate-grid">
      <article class="candidate-card" v-for="candidate in filteredCandidates" :key="candidate.id">
        <div class="candidate-top">
          <div>
            <div class="candidate-name">{{ candidate.name }}</div>
            <div class="candidate-meta">{{ candidate.role }} · {{ candidate.city }}</div>
          </div>
          <span class="pill status-pill">{{ candidate.status }}</span>
        </div>

        <p class="candidate-summary">{{ candidate.summary }}</p>

        <div class="tag-row">
          <span class="tag-chip" v-for="tag in candidate.skills" :key="tag">{{ tag }}</span>
        </div>

        <div class="candidate-footer">
          <span class="quality-text">解析质量 {{ candidate.quality }}</span>
          <div class="action-row">
            <RouterLink class="secondary-btn inline-btn" :to="candidate.detailTarget">详情</RouterLink>
            <RouterLink class="secondary-btn inline-btn" :to="candidate.editTarget">编辑</RouterLink>
            <RouterLink class="primary-btn inline-btn" :to="candidate.paperTarget">发卷</RouterLink>
          </div>
        </div>
      </article>
    </div>

    <div v-else class="state-card">没有符合筛选条件的候选人。</div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import {
  buildCandidateDetailPath,
  buildCandidateEditPath,
  buildPaperEditorPath,
  buildPaperRouteTarget
} from "../../components/admin/adminRouting";
import { loadCandidates, type CandidateCard } from "../../lib/gateway";

const route = useRoute();
const loading = ref(true);
const loadError = ref("");
const keyword = ref("");
const statusFilter = ref("全部状态");
const candidates = ref<CandidateCard[]>([]);

const candidateEntries = computed(() =>
  candidates.value.map((candidate) => ({
    ...candidate,
    detailTarget: buildCandidateDetailPath(candidate.id),
    editTarget: buildCandidateEditPath(candidate.id),
    paperTarget: {
      ...buildPaperRouteTarget(candidate.id),
      path: buildPaperEditorPath(candidate.paperId),
      query: {
        candidateId: candidate.id,
        candidateName: candidate.name
      }
    }
  }))
);

const filteredCandidates = computed(() => {
  const search = keyword.value.trim().toLowerCase();

  return candidateEntries.value.filter((candidate) => {
    const matchesStatus = statusFilter.value === "全部状态" || candidate.status === statusFilter.value;
    const matchesKeyword =
      !search ||
      [candidate.name, candidate.role, candidate.city, candidate.summary, ...candidate.skills]
        .join(" ")
        .toLowerCase()
        .includes(search);

    return matchesStatus && matchesKeyword;
  });
});

const nextActionCandidate = computed(
  () => candidateEntries.value.find((candidate) => candidate.status !== "已开考") ?? candidateEntries.value[0] ?? null
);

const metrics = computed(() => [
  { label: "总候选人", value: String(candidates.value.length) },
  { label: "待审核", value: String(candidates.value.filter((candidate) => candidate.status === "待审核").length) },
  { label: "待发卷", value: String(candidates.value.filter((candidate) => candidate.status === "待发卷").length) },
  { label: "已开考", value: String(candidates.value.filter((candidate) => candidate.status === "已开考").length) }
]);

function resetFilters() {
  keyword.value = "";
  statusFilter.value = "全部状态";
}

watch(
  () => route.query.status,
  (status) => {
    statusFilter.value = typeof status === "string" && status.length ? status : "全部状态";
  },
  { immediate: true }
);

async function loadCandidateCards() {
  loading.value = true;
  try {
    candidates.value = await loadCandidates(typeof route.query.taskId === "string" ? route.query.taskId : undefined);
    loadError.value = "";
  } catch {
    loadError.value = "候选人列表加载失败，等待后端接口恢复。";
  } finally {
    loading.value = false;
  }
}

watch(
  () => route.query.taskId,
  async () => {
    await loadCandidateCards();
  }
);

onMounted(async () => {
  await loadCandidateCards();
});
</script>

<style scoped>
.page-card {
  display: grid;
  gap: 22px;
  padding: 24px;
}

.page-head,
.candidate-top,
.candidate-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-title {
  margin: 16px 0 0;
}

.head-actions,
.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.toolbar {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 200px auto;
  gap: 14px;
}

.candidate-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.candidate-card,
.state-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.candidate-card {
  display: grid;
  gap: 14px;
}

.candidate-name {
  font-size: 1.06rem;
  font-weight: 700;
}

.candidate-meta,
.quality-text,
.state-card {
  color: var(--ink-soft);
}

.candidate-summary,
.state-card {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.inline-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 960px) {
  .page-head,
  .candidate-top,
  .candidate-footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid,
  .toolbar,
  .candidate-grid {
    grid-template-columns: 1fr;
  }
}
</style>
