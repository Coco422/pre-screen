<template>
  <section class="glass-card result-list-page">
    <div class="page-head">
      <div>
        <div class="pill">Results</div>
        <h2 class="section-title page-title">已完成考卷</h2>
      </div>
      <RouterLink class="secondary-btn" :to="{ name: 'admin-workbench' }">返回工作台</RouterLink>
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
          <AdminToneBadge :label="result.scoreBand.label" :tone="result.scoreBand.tone" />
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
                ? `共 ${result.riskPreview.total} 次异常，${result.riskPreview.items.slice(0, 2).map((item) => `${item.label} ${item.count} 次`).join(" · ")}`
                : "当前未记录异常行为"
            }}
          </span>
        </div>
      </RouterLink>
    </div>

    <div v-else class="state-card">暂时还没有已交卷结果。</div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import AdminScoreBar from "../../components/admin/AdminScoreBar.vue";
import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import { describeScoreBand, summarizeRiskSummary } from "../../components/admin/adminUi";
import { loadResultDetail, loadResults, type ResultSummary } from "../../lib/gateway";

const loading = ref(true);
const loadError = ref("");
const results = ref<ResultSummary[]>([]);
const riskPreviewMap = ref<Record<string, ReturnType<typeof summarizeRiskSummary>>>({});

const resultCards = computed(() =>
  results.value.map((result) => ({
    ...result,
    scoreBand: describeScoreBand(result.totalScore),
    riskPreview:
      riskPreviewMap.value[result.resultId] ??
      summarizeRiskSummary({
        event_count: 0,
        event_types: {}
      })
  }))
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
    loadError.value = error instanceof Error ? error.message : "结果列表加载失败。";
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
.risk-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-title {
  margin: 16px 0 0;
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
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.result-card {
  display: grid;
  gap: 14px;
  color: inherit;
}

.result-meta,
.state-card,
.risk-copy {
  color: var(--ink-soft);
}

.risk-row {
  align-items: flex-start;
}

.risk-copy {
  line-height: 1.6;
  text-align: right;
}

@media (max-width: 960px) {
  .page-head,
  .result-top,
  .risk-row {
    align-items: flex-start;
    flex-direction: column;
  }

  .result-grid {
    grid-template-columns: 1fr;
  }

  .risk-copy {
    text-align: left;
  }
}
</style>
