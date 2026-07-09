<template>
  <section v-if="result" class="result-detail-page">
    <article class="glass-card hero-card">
      <div class="page-head">
        <div>
          <div class="pill">Result Detail</div>
          <h2 class="section-title page-title">{{ result.candidate.name }}</h2>
          <p class="section-copy">{{ result.candidate.role }} · {{ formatTime(result.invitation.submittedAt) }}</p>
        </div>
        <div class="hero-badges">
          <AdminToneBadge :label="scoreBand.label" :tone="scoreBand.tone" />
          <AdminToneBadge :label="`风险 ${riskSummary.label}`" :tone="riskSummary.tone" />
          <RouterLink class="secondary-btn" :to="{ name: 'admin-results' }">返回结果列表</RouterLink>
        </div>
      </div>

      <div class="metric-grid">
        <article class="metric-tile">
          <div class="metric-value">{{ result.summary.totalScore }}</div>
          <div class="metric-label">总分</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ riskSummary.total }}</div>
          <div class="metric-label">异常事件</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ result.answers.length }}</div>
          <div class="metric-label">作答题数</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ result.coding?.summary.passedCount ?? 0 }}</div>
          <div class="metric-label">代码通过用例</div>
        </article>
      </div>
    </article>

    <section class="summary-grid">
      <article class="glass-card detail-card">
        <div class="panel-head">
          <h3>评分拆解</h3>
        </div>

        <div class="score-stack">
          <AdminScoreBar
            label="客观题"
            :value="`${result.summary.objectiveScore} 分`"
            :percent="scoreShare(result.summary.objectiveScore)"
            :tone="scoreBand.tone"
          />
          <AdminScoreBar
            label="主观题"
            :value="`${result.summary.subjectiveScore} 分`"
            :percent="scoreShare(result.summary.subjectiveScore)"
            :tone="scoreBand.tone"
          />
          <AdminScoreBar
            label="代码题"
            :value="`${result.summary.codingScore} 分`"
            :percent="scoreShare(result.summary.codingScore)"
            :tone="scoreBand.tone"
          />
        </div>
      </article>

      <article class="glass-card detail-card">
        <div class="panel-head">
          <h3>风险摘要</h3>
        </div>

        <div class="risk-summary">
          <p class="risk-copy">{{ riskNarrative }}</p>
          <div v-if="riskSummary.items.length" class="risk-chip-row">
            <AdminToneBadge
              v-for="item in riskSummary.items"
              :key="item.key"
              :label="`${item.label} ${item.count} 次`"
              :tone="item.tone"
            />
          </div>
          <div v-else class="risk-empty">本次作答未记录异常事件。</div>
        </div>
      </article>
    </section>

    <article class="glass-card detail-card">
      <div class="panel-head">
        <h3>作答详情</h3>
      </div>

      <div class="answer-list">
        <article class="answer-item" v-for="answer in result.answers" :key="answer.questionId || answer.title">
          <div class="answer-head">
            <div class="answer-title">
              <strong>{{ answer.title }}</strong>
              <AdminToneBadge :label="questionKindLabel(answer.kind)" :tone="questionKindTone(answer.kind)" />
            </div>
            <span class="pill">{{ answer.score }} 分</span>
          </div>
          <pre class="answer-body">{{ formatAnswer(answer.answer) }}</pre>
          <div class="answer-comment">{{ answer.comment || "暂无评语" }}</div>
        </article>
      </div>
    </article>

    <article v-if="result.coding" class="glass-card detail-card">
      <div class="panel-head">
        <h3>代码题运行结果</h3>
      </div>

      <div class="coding-grid">
        <AdminScoreBar
          label="得分"
          :value="`${result.coding.summary.totalScore}/${result.coding.summary.maxScore}`"
          :percent="codingPercent"
          :tone="codingPercent >= 80 ? 'success' : codingPercent >= 60 ? 'info' : 'warning'"
        />

        <div class="coding-meta">
          <div class="fact-row">
            <span>语言</span>
            <strong>{{ result.coding.language }}</strong>
          </div>
          <div class="fact-row">
            <span>通过</span>
            <strong>{{ result.coding.summary.passedCount }}</strong>
          </div>
          <div class="fact-row">
            <span>失败</span>
            <strong>{{ result.coding.summary.failedCount }}</strong>
          </div>
        </div>
      </div>
    </article>

    <article class="glass-card detail-card review-panel">
      <div class="panel-head">
        <h3>评分复核</h3>
        <AdminToneBadge
          :label="result.reviewStatus === 'reviewed' ? '已复核' : '待复核'"
          :tone="result.reviewStatus === 'reviewed' ? 'success' : 'warning'"
        />
      </div>

      <div class="review-form">
        <label class="field">
          <span>主观题最终分</span>
          <el-input-number v-model="finalSubjectiveScore" :min="0" :max="100" />
        </label>
        <label class="field">
          <span>复核备注</span>
          <el-input
            v-model="reviewNotesText"
            type="textarea"
            :rows="3"
            placeholder="可选，写入复核记录"
          />
        </label>
        <div class="review-actions">
          <button class="secondary-btn" type="button" :disabled="saving" @click="saveReview">
            {{ saving ? "保存中..." : "保存修分" }}
          </button>
          <button class="primary-btn" type="button" :disabled="saving" @click="decide('pass')">
            通过筛选
          </button>
          <button class="danger-btn" type="button" :disabled="saving" @click="decide('reject')">
            淘汰
          </button>
        </div>
        <p v-if="actionMessage" class="action-message" :class="actionMessageType">{{ actionMessage }}</p>
      </div>
    </article>
  </section>

  <section v-else class="glass-card detail-card">
    <div class="pill">Result Detail</div>
    <h2 class="section-title">{{ loadError || "正在加载结果详情..." }}</h2>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AdminScoreBar from "../../components/admin/AdminScoreBar.vue";
import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import { describeScoreBand, summarizeRiskSummary, type AdminTone } from "../../components/admin/adminUi";
import {
  completeScreening,
  loadResultDetail,
  reviewResult,
  type ResultDetail
} from "../../lib/gateway";

const route = useRoute();
const result = ref<ResultDetail | null>(null);
const loadError = ref("");
const finalSubjectiveScore = ref(0);
const reviewNotesText = ref("");
const saving = ref(false);
const actionMessage = ref("");
const actionMessageType = ref<"ok" | "err">("ok");

const scoreBand = computed(() => describeScoreBand(result.value?.summary.totalScore ?? 0));
const riskSummary = computed(() =>
  summarizeRiskSummary(
    result.value?.summary.riskSummary ?? {
      event_count: 0,
      event_types: {}
    }
  )
);
const riskNarrative = computed(() => {
  if (!riskSummary.value.total) {
    return "本次考试过程中没有记录到异常行为，风险信号较低。";
  }

  return `共记录 ${riskSummary.value.total} 次异常事件，建议重点关注 ${riskSummary.value.items
    .slice(0, 2)
    .map((item) => `${item.label}${item.count}次`)
    .join("、")}。`;
});
const codingPercent = computed(() => {
  if (!result.value?.coding?.summary.maxScore) {
    return 0;
  }

  return Math.round((result.value.coding.summary.totalScore / result.value.coding.summary.maxScore) * 100);
});

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

function formatAnswer(answer: unknown) {
  return typeof answer === "string" ? answer : JSON.stringify(answer, null, 2);
}

function scoreShare(value: number) {
  if (!result.value?.summary.totalScore) {
    return 0;
  }

  return Math.round((value / result.value.summary.totalScore) * 100);
}

function questionKindLabel(kind: string) {
  if (kind === "objective") {
    return "客观题";
  }
  if (kind === "subjective") {
    return "主观题";
  }
  if (kind === "coding") {
    return "代码题";
  }
  return "基础信息";
}

function questionKindTone(kind: string): AdminTone {
  if (kind === "coding") {
    return "info";
  }
  if (kind === "subjective") {
    return "warning";
  }
  if (kind === "objective") {
    return "success";
  }
  return "neutral";
}

async function reloadResult(resultId: string) {
  result.value = await loadResultDetail(resultId);
  finalSubjectiveScore.value = result.value.summary.subjectiveScore;
  reviewNotesText.value = (result.value.reviewNotes ?? []).join("\n");
  loadError.value = "";
}

async function saveReview() {
  if (!result.value) {
    return;
  }
  saving.value = true;
  actionMessage.value = "";
  try {
    const notes = reviewNotesText.value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    await reviewResult(result.value.resultId, {
      finalSubjectiveScore: finalSubjectiveScore.value,
      reviewNotes: notes
    });
    await reloadResult(result.value.resultId);
    actionMessage.value = "修分已保存";
    actionMessageType.value = "ok";
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : "保存失败";
    actionMessageType.value = "err";
  } finally {
    saving.value = false;
  }
}

async function decide(decision: "pass" | "reject") {
  if (!result.value) {
    return;
  }
  saving.value = true;
  actionMessage.value = "";
  try {
    const notes = reviewNotesText.value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean);
    await reviewResult(result.value.resultId, {
      finalSubjectiveScore: finalSubjectiveScore.value,
      reviewNotes: notes
    });
    await completeScreening(result.value.resultId, { decision, reviewNotes: notes });
    await reloadResult(result.value.resultId);
    actionMessage.value = decision === "pass" ? "已通过筛选" : "已淘汰";
    actionMessageType.value = "ok";
  } catch (error) {
    actionMessage.value = error instanceof Error ? error.message : "操作失败";
    actionMessageType.value = "err";
  } finally {
    saving.value = false;
  }
}

watch(
  () => route.params.resultId,
  async (resultId) => {
    if (typeof resultId !== "string") {
      result.value = null;
      return;
    }

    try {
      await reloadResult(resultId);
      actionMessage.value = "";
    } catch (error) {
      loadError.value = error instanceof Error ? error.message : "加载失败";
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.result-detail-page {
  display: grid;
  gap: 20px;
}

.hero-card,
.detail-card {
  padding: 24px;
}

.page-head,
.panel-head,
.answer-head,
.fact-row,
.hero-badges {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hero-badges {
  flex-wrap: wrap;
  justify-content: flex-end;
}

.page-title {
  margin: 16px 0 0;
}

.metric-grid,
.summary-grid {
  display: grid;
  gap: 16px;
}

.metric-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 20px;
}

.summary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.score-stack,
.answer-list,
.risk-summary {
  display: grid;
  gap: 16px;
}

.risk-copy,
.risk-empty,
.answer-comment {
  color: var(--ink-soft);
  line-height: 1.6;
}

.risk-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.answer-item {
  display: grid;
  gap: 12px;
  padding: 18px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.04);
}

.review-form {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
  color: var(--ink-soft);
}

.review-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.danger-btn {
  border: 1px solid rgba(176, 45, 62, 0.35);
  background: rgba(176, 45, 62, 0.08);
  color: #8f1f2f;
  border-radius: 999px;
  padding: 8px 16px;
  cursor: pointer;
}

.action-message.ok {
  color: #1f6b3a;
}

.action-message.err {
  color: #8f1f2f;
}

.answer-title {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.answer-body {
  margin: 0;
  padding: 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.76);
  white-space: pre-wrap;
  word-break: break-word;
}

.coding-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(220px, 0.7fr);
  gap: 18px;
}

.coding-meta {
  display: grid;
  gap: 12px;
}

.fact-row {
  padding: 12px 0;
  border-bottom: 1px solid rgba(20, 33, 61, 0.06);
}

.fact-row span {
  color: var(--ink-soft);
}

@media (max-width: 960px) {
  .page-head,
  .panel-head,
  .answer-head,
  .fact-row,
  .hero-badges {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid,
  .summary-grid,
  .coding-grid {
    grid-template-columns: 1fr;
  }
}
</style>
