<template>
  <section v-if="profile" class="detail-grid">
    <article class="glass-card detail-card detail-card--hero">
      <div class="detail-head">
        <div>
          <div class="pill">Candidate</div>
          <h2 class="section-title detail-title">{{ profile.name }}</h2>
          <p class="detail-meta">{{ profile.role }} · {{ profile.email || "邮箱待补齐" }} · {{ profile.city }}</p>
        </div>
        <div class="button-row">
          <RouterLink class="secondary-btn" :to="{ name: 'admin-candidates' }">返回列表</RouterLink>
          <RouterLink class="secondary-btn" :to="editTarget">编辑画像</RouterLink>
          <RouterLink class="primary-btn" :to="paperTarget">去发卷</RouterLink>
        </div>
      </div>

      <div class="tag-row">
        <AdminToneBadge :label="profile.status" :tone="statusTone" />
        <AdminToneBadge :label="`解析质量 ${profile.quality}`" :tone="signal.tone" />
        <AdminToneBadge :label="signal.readinessLabel" :tone="signal.tone" />
        <span class="tag-chip" v-for="skill in profile.skills" :key="skill">{{ skill }}</span>
      </div>

      <div class="signal-grid">
        <article class="signal-card">
          <div class="signal-title">推荐动作</div>
          <div class="action-stack">
            <article class="action-card" v-for="action in actionItems" :key="action.title">
              <div class="action-copy">
                <AdminToneBadge :label="action.eyebrow" :tone="action.tone" />
                <div class="action-title">{{ action.title }}</div>
                <div class="action-detail">{{ action.detail }}</div>
              </div>
              <RouterLink v-if="action.to" class="secondary-btn inline-btn" :to="action.to">{{ action.cta }}</RouterLink>
            </article>
          </div>
        </article>

        <article class="signal-card">
          <div class="signal-title">解析质量</div>
          <AdminScoreBar
            label="画像可用度"
            :value="signal.qualityScore"
            :percent="signal.qualityScore"
            :detail="signal.qualityLabel"
            :tone="signal.tone"
          />
          <div class="metric-list">
            <div class="metric-tile">
              <div class="metric-value">{{ profile.parseMetrics.firstPageCharacters }}</div>
              <div class="metric-label">首页字符</div>
            </div>
            <div class="metric-tile">
              <div class="metric-value">{{ profile.parseMetrics.multimodalPages }}</div>
              <div class="metric-label">补读页数</div>
            </div>
            <div class="metric-tile">
              <div class="metric-value">{{ profile.availableInDays ?? "-" }}</div>
              <div class="metric-label">预计到岗</div>
            </div>
          </div>
        </article>
      </div>

      <div class="detail-section project-section">
        <div class="detail-section-head">
          <h3>项目摘要</h3>
          <AdminToneBadge :label="projectSummaryState.label" :tone="projectSummaryState.tone" />
        </div>
        <p>{{ profile.projectSummary }}</p>
      </div>
    </article>

    <article class="glass-card detail-card sidebar-card">
      <div class="pill">Review</div>

      <div class="detail-section">
        <div class="detail-section-head">
          <h3>解析风险</h3>
          <AdminToneBadge :label="`${riskItems.length} 项关注`" :tone="riskItems.length ? 'warning' : 'success'" />
        </div>
        <div v-if="riskItems.length" class="risk-list">
          <article class="risk-item" v-for="risk in riskItems" :key="risk.label">
            <AdminToneBadge :label="risk.label" :tone="risk.tone" />
            <p>{{ risk.detail }}</p>
          </article>
        </div>
        <p v-else class="helper-copy">当前解析信号稳定，没有额外风险提醒。</p>
      </div>

      <div class="detail-section">
        <h3>人工复核备注</h3>
        <ul class="note-list">
          <li v-for="note in profile.reviewNotes" :key="note">{{ note }}</li>
        </ul>
      </div>

      <div class="detail-section">
        <h3>联系与背景</h3>
        <div class="fact-list">
          <div class="fact-row">
            <span>手机号</span>
            <strong>{{ profile.phone || "待补齐" }}</strong>
          </div>
          <div class="fact-row">
            <span>兴趣</span>
            <strong>{{ profile.hobbies.length ? profile.hobbies.join(" / ") : "暂无" }}</strong>
          </div>
          <div class="fact-row">
            <span>邮箱</span>
            <strong>{{ profile.email || "待补齐" }}</strong>
          </div>
        </div>
      </div>
    </article>
  </section>

  <section v-else class="glass-card loading-card">
    <div class="pill">Candidate</div>
    <h2 class="section-title">{{ loadError || "正在加载候选人详情..." }}</h2>
    <p class="section-copy">详情页会以当前路由候选人为准，避免切换时残留上一位候选人的内容。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AdminScoreBar from "../../components/admin/AdminScoreBar.vue";
import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import {
  buildCandidateEditPath,
  buildPaperEditorPath,
  buildPaperRouteTarget,
  buildResultDetailPath
} from "../../components/admin/adminRouting";
import {
  buildCandidateActionKeys,
  buildCandidateRiskItems,
  buildCandidateSignal,
  type AdminTone
} from "../../components/admin/adminUi";
import { loadCandidateDetail, type CandidateDetail } from "../../lib/gateway";

type CandidateDraft = Pick<CandidateDetail, "name" | "role" | "email" | "city" | "skills" | "projectSummary" | "reviewNotes">;

const route = useRoute();
const profile = ref<CandidateDetail | null>(null);
const loadError = ref("");
let latestRequestId = 0;

const candidateId = computed(() => (typeof route.params.candidateId === "string" ? route.params.candidateId : ""));
const editTarget = computed(() => buildCandidateEditPath(candidateId.value));

const paperTarget = computed(() => {
  const target = buildPaperRouteTarget(candidateId.value);

  return {
    ...target,
    path: buildPaperEditorPath(profile.value?.paperId),
    query: {
      candidateId: candidateId.value,
      candidateName: profile.value?.name ?? ""
    }
  };
});

const signal = computed(() =>
  profile.value
    ? buildCandidateSignal(profile.value)
    : {
        qualityScore: 0,
        qualityLabel: "",
        readinessLabel: "",
        tone: "neutral" as AdminTone
      }
);
const riskItems = computed(() => (profile.value ? buildCandidateRiskItems(profile.value) : []));
const statusTone = computed(() => {
  if (!profile.value) {
    return "neutral";
  }
  if (profile.value.status === "待发卷" || profile.value.status === "已交卷") {
    return "success";
  }
  if (profile.value.status === "解析中") {
    return "info";
  }
  if (profile.value.status === "解析失败") {
    return "danger";
  }
  return "warning";
});
const projectSummaryState = computed(() => {
  if (!profile.value?.projectSummary || profile.value.projectSummary.includes("暂无")) {
    return { label: "摘要待补强", tone: "warning" as AdminTone };
  }
  if (profile.value.projectSummary.length < 60) {
    return { label: "摘要偏短", tone: "warning" as AdminTone };
  }
  return { label: "摘要可用", tone: "success" as AdminTone };
});

const actionItems = computed(() => {
  const currentProfile = profile.value;
  if (!currentProfile) {
    return [];
  }

  return buildCandidateActionKeys(currentProfile).map((key) => {
    if (key === "publish") {
      return {
        eyebrow: "优先处理",
        title: currentProfile.paperId ? "确认并发布考试入口" : "生成考卷并发布考试入口",
        detail: "候选人画像已可用，下一步就是把考试入口发出去。",
        cta: "去发卷",
        to: paperTarget.value,
        tone: "success" as AdminTone
      };
    }

    if (key === "edit") {
      return {
        eyebrow: "建议修正",
        title: "补齐候选人画像",
        detail: "存在缺失字段或解析风险，先修正画像能提升后续判断质量。",
        cta: "编辑画像",
        to: editTarget.value,
        tone: "warning" as AdminTone
      };
    }

    if (key === "view_result") {
      return {
        eyebrow: "已完成",
        title: "查看考试结果",
        detail: "候选人已交卷，优先进入结果页判断评分与风险事件。",
        cta: "查看结果",
        to: currentProfile.resultId ? buildResultDetailPath(currentProfile.resultId) : undefined,
        tone: "info" as AdminTone
      };
    }

    if (key === "view_entry") {
      return {
        eyebrow: "已发布",
        title: "查看考试入口状态",
        detail: "考试入口已经生成，建议确认链接与验证码后继续催考。",
        cta: "查看入口",
        to: paperTarget.value,
        tone: "info" as AdminTone
      };
    }

    return {
      eyebrow: "跟进提醒",
      title: "安排候选人跟进",
      detail: currentProfile.invitationToken ? "入口已生成，建议尽快发送并确认开考时间。" : "完成画像后及时推进下一步，避免候选人冷掉。",
      cta: "查看画像",
      to: currentProfile.invitationToken ? paperTarget.value : editTarget.value,
      tone: "neutral" as AdminTone
    };
  });
});

function readCandidateDraft(targetCandidateId: string): Partial<CandidateDraft> | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(`admin-candidate-draft:${targetCandidateId}`);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as Partial<CandidateDraft>;
  } catch {
    return null;
  }
}

function applyCandidateDraft(detail: CandidateDetail, targetCandidateId: string): CandidateDetail {
  const draft = readCandidateDraft(targetCandidateId);
  if (!draft) {
    return detail;
  }

  return {
    ...detail,
    ...draft,
    skills: Array.isArray(draft.skills) && draft.skills.length ? draft.skills : detail.skills,
    reviewNotes: Array.isArray(draft.reviewNotes) && draft.reviewNotes.length ? draft.reviewNotes : detail.reviewNotes
  };
}

watch(
  candidateId,
  async (nextCandidateId) => {
    if (!nextCandidateId) {
      profile.value = null;
      loadError.value = "";
      return;
    }

    const requestId = ++latestRequestId;
    profile.value = null;
    loadError.value = "";

    try {
      const detail = await loadCandidateDetail(nextCandidateId);
      if (requestId !== latestRequestId) {
        return;
      }

      profile.value = applyCandidateDraft(detail, nextCandidateId);
    } catch {
      if (requestId !== latestRequestId) {
        return;
      }

      loadError.value = "候选人详情加载失败，请稍后重试。";
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(320px, 0.92fr);
  gap: 24px;
}

.detail-card {
  padding: 24px;
}

.detail-card--hero {
  display: grid;
  gap: 20px;
}

.detail-head,
.button-row,
.detail-section-head,
.fact-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.button-row {
  flex-wrap: wrap;
}

.detail-title {
  margin: 16px 0 0;
  font-size: 2rem;
}

.detail-meta,
.detail-section p,
.note-list,
.helper-copy,
.action-detail,
.risk-item p {
  color: var(--ink-soft);
  line-height: 1.7;
}

.detail-meta {
  margin: 12px 0 0;
}

.tag-row,
.action-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-chip {
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
}

.signal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.signal-card,
.action-card,
.risk-item {
  padding: 18px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.signal-card {
  display: grid;
  gap: 16px;
}

.signal-title,
.action-title {
  font-weight: 700;
}

.action-stack,
.risk-list {
  display: grid;
  gap: 12px;
}

.action-card {
  display: grid;
  gap: 14px;
}

.action-copy {
  display: grid;
  gap: 10px;
}

.metric-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.project-section {
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.88), rgba(244, 246, 248, 0.88));
}

.detail-section {
  display: grid;
  gap: 10px;
}

.detail-section h3 {
  margin: 0;
}

.sidebar-card {
  display: grid;
  align-content: start;
  gap: 24px;
}

.note-list {
  margin: 0;
  padding-left: 18px;
}

.fact-list {
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

.loading-card {
  padding: 24px;
}

@media (max-width: 960px) {
  .detail-grid,
  .signal-grid,
  .metric-list {
    grid-template-columns: 1fr;
  }

  .detail-head,
  .button-row,
  .detail-section-head,
  .fact-row {
    flex-direction: column;
  }
}
</style>
