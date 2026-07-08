<template>
  <section class="dashboard-page">
    <div v-if="loading" class="dashboard-state-card">加载中</div>
    <div v-else-if="loadError" class="dashboard-error-banner" role="alert">
      <strong>工作台数据加载失败</strong>
      <span>{{ loadError }}</span>
    </div>

    <template v-else>
      <section class="dashboard-metrics">
        <article v-for="metric in metrics" :key="metric.label" class="dashboard-metric">
          <span
            class="dashboard-metric__icon"
            :style="{ '--metric-color': metric.color, '--metric-bg': metric.bg }"
            aria-hidden="true"
          >
            <el-icon><component :is="metric.icon" /></el-icon>
          </span>
          <span class="dashboard-metric__copy">
            <span>{{ metric.label }}</span>
            <strong>{{ metric.value }}</strong>
          </span>
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
              <el-tooltip :content="item.name" placement="top" :show-after="300">
                <strong class="dashboard-list__text">{{ item.name }}</strong>
              </el-tooltip>
              <el-tooltip :content="item.role" placement="top" :show-after="300">
                <span class="dashboard-list__text">{{ item.role }}</span>
              </el-tooltip>
              <el-tooltip :content="item.status" placement="top" :show-after="300">
                <span class="dashboard-list__text">{{ item.status }}</span>
              </el-tooltip>
              <el-tooltip :content="formatDateTime(item.resumeUploadedAt)" placement="top" :show-after="300">
                <time class="dashboard-list__text">{{ formatDateTime(item.resumeUploadedAt) }}</time>
              </el-tooltip>
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
              <el-tooltip :content="item.name" placement="top" :show-after="300">
                <strong class="dashboard-list__text">{{ item.name }}</strong>
              </el-tooltip>
              <el-tooltip :content="item.role" placement="top" :show-after="300">
                <span class="dashboard-list__text">{{ item.role }}</span>
              </el-tooltip>
              <el-tooltip :content="item.status" placement="top" :show-after="300">
                <span class="dashboard-list__text">{{ item.status }}</span>
              </el-tooltip>
              <el-tooltip :content="formatDateTime(item.profileCompletedAt)" placement="top" :show-after="300">
                <time class="dashboard-list__text">{{ formatDateTime(item.profileCompletedAt) }}</time>
              </el-tooltip>
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
              <el-tooltip :content="item.candidateName" placement="top" :show-after="300">
                <strong class="dashboard-list__text">{{ item.candidateName }}</strong>
              </el-tooltip>
              <el-tooltip :content="item.role" placement="top" :show-after="300">
                <span class="dashboard-list__text">{{ item.role }}</span>
              </el-tooltip>
              <el-tooltip :content="`${item.totalScore} 分`" placement="top" :show-after="300">
                <span class="dashboard-list__text">{{ item.totalScore }} 分</span>
              </el-tooltip>
              <el-tooltip :content="formatDateTime(item.submittedAt)" placement="top" :show-after="300">
                <time class="dashboard-list__text">{{ formatDateTime(item.submittedAt) }}</time>
              </el-tooltip>
            </RouterLink>
          </div>
          <div v-else class="dashboard-empty">当前还没有已交卷结果。</div>
        </article>
      </section>
    </template>
  </section>
</template>

<script setup lang="ts">
import type { Component } from "vue";

import { DocumentChecked, Finished, Stopwatch, Tickets, UserFilled } from "@element-plus/icons-vue";
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

type DashboardMetric = {
  label: string;
  value: string;
  icon: Component;
  color: string;
  bg: string;
};

const metrics = computed<DashboardMetric[]>(() => [
  { label: "筛选中候选人", value: String(dashboard.value.metrics.screeningCandidateCount), icon: UserFilled, color: "#2f6cf6", bg: "#eaf2ff" },
  { label: "待发卷人数", value: String(dashboard.value.metrics.pendingPublishCount), icon: Tickets, color: "#2f6cf6", bg: "#eef5ff" },
  { label: "进行中考试", value: String(dashboard.value.metrics.examInProgressCount), icon: Stopwatch, color: "#246ee9", bg: "#e9f2ff" },
  { label: "已交卷", value: String(dashboard.value.metrics.submittedCount), icon: DocumentChecked, color: "#24a47a", bg: "#e8f8f2" },
  { label: "已完成筛选", value: String(dashboard.value.metrics.screeningCompletedCount), icon: Finished, color: "#f25f5c", bg: "#fff0f0" }
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
  gap: 16px;
}

.dashboard-state-card,
.dashboard-error-banner {
  border: 1px solid #d7e4f4;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 2px 8px rgba(23, 42, 76, 0.04);
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
  gap: 16px;
}

.dashboard-metric {
  display: flex;
  align-items: center;
  gap: 24px;
  min-height: 96px;
  padding: 18px 20px;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 2px 10px rgba(24, 47, 82, 0.04);
}

.dashboard-metric__icon {
  display: grid;
  place-items: center;
  flex: none;
  width: 44px;
  height: 44px;
  border-radius: 8px;
  background: var(--metric-bg);
  color: var(--metric-color);
  font-size: 24px;
}

.dashboard-metric__copy {
  display: grid;
  gap: 8px;
  min-width: 0;
}

.dashboard-metric__copy span {
  color: #5f7090;
  font-size: 15px;
  font-weight: 700;
  line-height: 1.2;
}

.dashboard-metric__copy strong {
  color: #13243c;
  font-size: 28px;
  line-height: 1;
  letter-spacing: 0;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.dashboard-panel {
  display: grid;
  gap: 12px;
  align-content: start;
  max-height: calc(100vh - 204px);
  overflow: hidden;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
}

.dashboard-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.dashboard-panel__head h2 {
  margin: 0;
  color: #15253d;
  font-size: 18px;
  font-weight: 800;
}

.dashboard-panel__head a {
  color: #2a6cf0;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.dashboard-list {
  display: grid;
  overflow: auto;
}

.dashboard-list__item {
  display: grid;
  grid-template-columns: minmax(54px, 0.8fr) minmax(82px, 1.2fr) minmax(64px, 0.8fr) minmax(72px, 0.9fr);
  align-items: center;
  gap: 10px;
  min-height: 52px;
  padding: 10px 2px;
  border-bottom: 1px solid #edf2f8;
}

.dashboard-list__item strong {
  color: #16263d;
  font-size: 14px;
  font-weight: 700;
}

.dashboard-list__text {
  display: block;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dashboard-list__item span,
.dashboard-list__item time {
  color: #62728d;
  font-size: 13px;
  line-height: 1.4;
}

.dashboard-list__item time {
  color: #7b8799;
  text-align: right;
}

.dashboard-empty {
  padding: 16px;
  border-bottom: 1px solid #edf2f8;
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
    align-items: flex-start;
  }

  .dashboard-list__item {
    grid-template-columns: 1fr;
  }

  .dashboard-list__item time {
    text-align: left;
  }
}
</style>
