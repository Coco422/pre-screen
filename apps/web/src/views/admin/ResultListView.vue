<template>
  <section class="glass-card result-list-page">
    <div class="page-head">
      <div>
        <h2 class="section-title page-title">结果中心</h2>
        <p class="page-meta">含已通过 / 已淘汰档案，可随时回看答卷与评分</p>
      </div>
      <div class="head-actions">
        <el-select v-model="decisionFilter" clearable placeholder="全部结论" style="width: 140px">
          <el-option label="待复核" value="pending" />
          <el-option label="已通过" value="pass" />
          <el-option label="已淘汰" value="reject" />
        </el-select>
        <RouterLink class="secondary-btn" :to="{ name: 'admin-dashboard' }">返回工作台</RouterLink>
      </div>
    </div>

    <div v-if="loading" class="state-card">加载中</div>
    <div v-else-if="loadError" class="state-card">{{ loadError }}</div>

    <div v-else-if="resultCards.length" class="result-grid">
      <RouterLink
        v-for="result in resultCards"
        :key="result.resultId"
        class="result-card"
        :to="{ name: 'admin-result-detail', params: { resultId: result.resultId } }"
      >
        <div class="result-top">
          <div>
            <strong>{{ result.candidateName }}</strong>
            <div class="result-meta">{{ result.role }}</div>
          </div>
          <div class="badge-col">
            <AdminToneBadge :label="result.decisionLabel" :tone="result.decisionTone" />
            <AdminToneBadge :label="result.scoreBand.label" :tone="result.scoreBand.tone" />
          </div>
        </div>

        <AdminScoreBar
          label="总分"
          :value="`${result.totalScore} 分`"
          :percent="scorePercent(result.totalScore)"
          :detail="result.scoreBand.detail"
          :tone="result.scoreBand.tone"
        />

        <div class="result-meta">{{ formatTime(result.submittedAt) }}</div>

        <div class="risk-row">
          <AdminToneBadge :label="`风险 ${result.riskPreview.label}`" :tone="result.riskPreview.tone" />
          <span class="risk-copy">
            {{
              result.riskPreview.total
                ? `共 ${result.riskPreview.total} 次异常，${result.riskPreview.items
                    .slice(0, 2)
                    .map((item) => `${item.label} ${item.count} 次`)
                    .join(" · ")}`
                : "当前未记录异常行为"
            }}
          </span>
        </div>
      </RouterLink>
    </div>

    <div v-else class="state-card">当前筛选下没有结果。已淘汰候选人仍会保留在「已淘汰」筛选中供回看。</div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import AdminScoreBar from "../../components/admin/AdminScoreBar.vue";
import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import {
  describeScoreBand,
  summarizeRiskSummary,
  type AdminTone
} from "../../components/admin/adminUi";
import { loadResultDetail, loadResults, type ResultSummary } from "../../lib/gateway";

const loading = ref(true);
const loadError = ref("");
const results = ref<ResultSummary[]>([]);
const riskPreviewMap = ref<Record<string, ReturnType<typeof summarizeRiskSummary>>>({});
const decisionFilter = ref("");

function decisionMeta(result: ResultSummary): { label: string; tone: AdminTone; key: string } {
  if (result.screeningDecision === "pass") {
    return { label: "已通过", tone: "success", key: "pass" };
  }
  if (result.screeningDecision === "reject") {
    return { label: "已淘汰", tone: "danger", key: "reject" };
  }
  if (result.reviewStatus === "reviewed") {
    return { label: "已复核", tone: "info", key: "pending" };
  }
  return { label: "待复核", tone: "warning", key: "pending" };
}

const resultCards = computed(() =>
  results.value
    .map((result) => {
      const decision = decisionMeta(result);
      return {
        ...result,
        scoreBand: describeScoreBand(result.totalScore),
        riskPreview:
          riskPreviewMap.value[result.resultId] ??
          summarizeRiskSummary({
            event_count: 0,
            event_types: {}
          }),
        decisionLabel: decision.label,
        decisionTone: decision.tone,
        decisionKey: decision.key
      };
    })
    .filter((result) => !decisionFilter.value || result.decisionKey === decisionFilter.value)
);

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function scorePercent(value: number) {
  return Math.min(100, Math.max(0, Math.round(value)));
}

async function hydrateRiskPreview(items: ResultSummary[]) {
  const settled = await Promise.allSettled(items.map((item) => loadResultDetail(item.resultId)));
  const nextMap: Record<string, ReturnType<typeof summarizeRiskSummary>> = {};

  settled.forEach((entry, index) => {
    if (entry.status !== "fulfilled") {
      return;
    }

    nextMap[items[index].resultId] = summarizeRiskSummary(entry.value.summary.riskSummary);
  });

  riskPreviewMap.value = nextMap;
}

onMounted(async () => {
  loading.value = true;
  try {
    results.value = await loadResults();
    loadError.value = "";
    await hydrateRiskPreview(results.value);
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "加载失败";
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.result-list-page {
  display: grid;
  gap: 20px;
  padding: 24px;
}

.page-head,
.result-top,
.risk-row,
.head-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  margin: 8px 0 0;
}

.page-meta,
.result-meta,
.risk-copy {
  color: var(--ink-soft);
}

.result-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.result-card,
.state-card {
  padding: 20px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  display: grid;
  gap: 12px;
  text-decoration: none;
  color: inherit;
}

.badge-col {
  display: grid;
  gap: 6px;
  justify-items: end;
}

@media (max-width: 900px) {
  .result-grid {
    grid-template-columns: 1fr;
  }
}
</style>
