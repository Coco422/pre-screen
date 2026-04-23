<template>
  <section class="dashboard-page">
    <div v-if="loading" class="dashboard-state-card">正在同步工作台数据...</div>
    <div v-else-if="loadError" class="dashboard-error-banner" role="alert">
      <strong>工作台数据加载失败</strong>
      <span>{{ loadError }}</span>
    </div>

    <template v-else>
      <section class="dashboard-metrics">
        <article v-for="metric in metrics" :key="metric.label" class="dashboard-metric">
          <span>{{ metric.label }}</span>
          <strong>{{ metric.value }}</strong>
        </article>
      </section>

      <section class="dashboard-grid">
        <article class="dashboard-panel">
          <div class="dashboard-panel__head">
            <h2>筛选中候选人</h2>
            <RouterLink :to="{ name: 'admin-candidates', query: { status: '待审核' } }">查看全部</RouterLink>
          </div>

          <div v-if="dashboard.screeningCandidates.length" class="dashboard-list">
            <RouterLink v-for="item in dashboard.screeningCandidates" :key="item.candidateId" class="dashboard-list__item" :to="item.target">
              <div>
                <strong>{{ item.name }}</strong>
                <p>{{ item.role }} · {{ item.status }}</p>
              </div>
              <span>{{ formatDateTime(item.resumeUploadedAt) }}</span>
            </RouterLink>
          </div>
          <div v-else class="dashboard-empty">当前没有筛选中的候选人。</div>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__head">
            <h2>待发卷候选人</h2>
            <RouterLink :to="{ name: 'admin-candidates', query: { status: '待发卷' } }">查看全部</RouterLink>
          </div>

          <div v-if="dashboard.pendingPublishCandidates.length" class="dashboard-list">
            <RouterLink v-for="item in dashboard.pendingPublishCandidates" :key="item.candidateId" class="dashboard-list__item" :to="item.target">
              <div>
                <strong>{{ item.name }}</strong>
                <p>{{ item.role }} · {{ item.status }}</p>
              </div>
              <span>{{ formatDateTime(item.profileCompletedAt) }}</span>
            </RouterLink>
          </div>
          <div v-else class="dashboard-empty">当前没有待发卷候选人。</div>
        </article>

        <article class="dashboard-panel">
          <div class="dashboard-panel__head">
            <h2>已交卷</h2>
            <RouterLink :to="{ name: 'admin-results' }">查看全部</RouterLink>
          </div>

          <div v-if="dashboard.submittedResults.length" class="dashboard-list">
            <RouterLink v-for="item in dashboard.submittedResults" :key="item.resultId" class="dashboard-list__item" :to="item.target">
              <div>
                <strong>{{ item.candidateName }}</strong>
                <p>{{ item.role }} · {{ item.status }}</p>
              </div>
              <span>{{ item.totalScore }} 分 · {{ formatDateTime(item.submittedAt) }}</span>
            </RouterLink>
          </div>
          <div v-else class="dashboard-empty">当前还没有已交卷结果。</div>
        </article>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { loadDashboard, type AdminDashboard } from "../../lib/gateway";

const loading = ref(true);
const loadError = ref("");
const dashboard = ref<AdminDashboard>({
  metrics: {
    screeningCandidateCount: 0,
    pendingPublishCount: 0,
    examInProgressCount: 0,
    submittedCount: 0,
    screeningCompletedCount: 0
  },
  screeningCandidates: [],
  pendingPublishCandidates: [],
  submittedResults: []
});

const metrics = computed(() => [
  { label: "筛选中候选人", value: String(dashboard.value.metrics.screeningCandidateCount) },
  { label: "待发卷人数", value: String(dashboard.value.metrics.pendingPublishCount) },
  { label: "进行中考试", value: String(dashboard.value.metrics.examInProgressCount) },
  { label: "已交卷", value: String(dashboard.value.metrics.submittedCount) },
  { label: "已完成筛选", value: String(dashboard.value.metrics.screeningCompletedCount) }
]);

function formatDateTime(value?: string) {
  if (!value) {
    return "时间待补齐";
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

onMounted(async () => {
  loading.value = true;
  loadError.value = "";

  try {
    dashboard.value = await loadDashboard();
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "请稍后重试。";
  }
  loading.value = false;
});
</script>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 18px;
}

.dashboard-state-card,
.dashboard-error-banner,
.dashboard-panel,
.dashboard-metric {
  border: 1px solid #d7e4f4;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 12px 28px rgba(23, 42, 76, 0.05);
}

.dashboard-state-card,
.dashboard-error-banner {
  padding: 18px 20px;
}

.dashboard-error-banner {
  display: grid;
  gap: 6px;
  color: #8a2430;
  border-color: #f1c7cc;
  background: #fff8f8;
}

.dashboard-metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.dashboard-metric {
  display: grid;
  gap: 10px;
  padding: 18px;
}

.dashboard-metric span {
  color: #5f7090;
  font-size: 13px;
}

.dashboard-metric strong {
  color: #13243c;
  font-size: 32px;
  letter-spacing: -0.04em;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.dashboard-panel {
  display: grid;
  gap: 16px;
  padding: 18px;
}

.dashboard-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-panel__head h2 {
  margin: 0;
  color: #15253d;
  font-size: 18px;
}

.dashboard-panel__head a {
  color: #2a6cf0;
  white-space: nowrap;
}

.dashboard-list {
  display: grid;
  gap: 10px;
}

.dashboard-list__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #e1ebf7;
  border-radius: 12px;
  background: #f8fbff;
}

.dashboard-list__item strong {
  color: #16263d;
}

.dashboard-list__item p,
.dashboard-list__item span {
  margin: 6px 0 0;
  color: #62728d;
  font-size: 13px;
}

.dashboard-list__item span {
  margin: 0;
  text-align: right;
  white-space: nowrap;
}

.dashboard-empty {
  padding: 16px;
  border-radius: 12px;
  background: #f8fbff;
  color: #63738f;
}

@media (max-width: 1100px) {
  .dashboard-metrics,
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .dashboard-panel__head,
  .dashboard-list__item {
    flex-direction: column;
    align-items: flex-start;
  }

  .dashboard-list__item span {
    text-align: left;
  }
}
</style>
