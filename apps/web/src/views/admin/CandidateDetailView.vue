<template>
  <section v-if="profile" class="candidate-shell">
    <header class="console-header">
      <div class="header-copy">
        <div class="header-eyebrow">Candidate Review</div>
        <h1 class="header-title">{{ profile.name }}</h1>
        <p class="header-meta">{{ profile.role }} · {{ profile.city }} · {{ profile.email || "邮箱待补齐" }}</p>
      </div>

      <div class="header-actions">
        <RouterLink class="ghost-btn" :to="{ name: 'admin-candidates' }">返回列表</RouterLink>
        <RouterLink class="ghost-btn" :to="editTarget">编辑画像</RouterLink>
        <RouterLink class="primary-btn" :to="paperTarget">去发卷</RouterLink>
      </div>
    </header>

    <div class="status-strip">
      <AdminToneBadge :label="profile.status" :tone="statusTone" />
      <AdminToneBadge :label="`解析质量 ${profile.quality}`" :tone="signal.tone" />
      <AdminToneBadge :label="signal.readinessLabel" :tone="signal.tone" />
      <span class="status-note">{{ projectSummaryState.label }}</span>
      <span class="skill-line">{{ profile.skills.join(" / ") }}</span>
    </div>

    <section class="candidate-console">
      <div class="console-column">
        <article class="console-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">候选人总览</p>
              <h2>{{ profile.name }}</h2>
            </div>
            <div class="score-box">
              <span>{{ signal.qualityScore }}</span>
              <small>画像分</small>
            </div>
          </div>

          <p class="panel-summary">{{ profile.projectSummary }}</p>

          <div class="metric-grid">
            <article class="metric-card">
              <strong>{{ profile.parseMetrics.firstPageCharacters }}</strong>
              <span>首页字符</span>
            </article>
            <article class="metric-card">
              <strong>{{ profile.parseMetrics.multimodalPages }}</strong>
              <span>补读页数</span>
            </article>
            <article class="metric-card">
              <strong>{{ profile.availableInDays ?? "-" }}</strong>
              <span>到岗天数</span>
            </article>
          </div>
        </article>

        <article class="console-panel">
          <div class="panel-head panel-head--compact">
            <h3>基础档案</h3>
            <AdminToneBadge :label="signal.qualityLabel" :tone="signal.tone" />
          </div>

          <dl class="fact-grid">
            <div class="fact-item">
              <dt>邮箱</dt>
              <dd>{{ profile.email || "待补齐" }}</dd>
            </div>
            <div class="fact-item">
              <dt>手机号</dt>
              <dd>{{ profile.phone || "待补齐" }}</dd>
            </div>
            <div class="fact-item">
              <dt>城市</dt>
              <dd>{{ profile.city || "-" }}</dd>
            </div>
            <div class="fact-item">
              <dt>兴趣</dt>
              <dd>{{ profile.hobbies.length ? profile.hobbies.join(" / ") : "暂无" }}</dd>
            </div>
            <div class="fact-item">
              <dt>身高</dt>
              <dd>{{ profile.heightCm == null ? "-" : `${profile.heightCm} cm` }}</dd>
            </div>
            <div class="fact-item">
              <dt>体重</dt>
              <dd>{{ profile.weightKg == null ? "-" : `${profile.weightKg} kg` }}</dd>
            </div>
          </dl>
        </article>

        <article class="console-panel">
          <div class="panel-head panel-head--compact">
            <h3>解析信号</h3>
            <AdminToneBadge :label="`${riskItems.length} 项关注`" :tone="riskItems.length ? 'warning' : 'success'" />
          </div>
          <AdminScoreBar
            label="推进建议"
            :value="signal.qualityScore"
            :percent="signal.qualityScore"
            :detail="signal.readinessLabel"
            :tone="signal.tone"
          />
        </article>
      </div>

      <div class="console-column">
        <article class="console-panel">
          <div class="panel-head panel-head--compact">
            <div>
              <p class="panel-kicker">画像档案</p>
              <h3>结构画像</h3>
            </div>
            <span class="panel-state">{{ profile.analysis.missingFields.length ? "待补字段" : "字段齐全" }}</span>
          </div>

          <div class="archive-groups">
            <section class="archive-group">
              <h4>关注主题</h4>
              <div class="chip-grid">
                <span v-for="item in profile.analysis.focusTopics" :key="item" class="line-chip">{{ item }}</span>
                <span v-if="!profile.analysis.focusTopics.length" class="line-chip line-chip--muted">暂无</span>
              </div>
            </section>

            <section class="archive-group">
              <h4>优势亮点</h4>
              <ul class="line-list">
                <li v-for="item in profile.analysis.strengths" :key="item">{{ item }}</li>
                <li v-if="!profile.analysis.strengths.length">暂无</li>
              </ul>
            </section>

            <section class="archive-group">
              <h4>推荐语言</h4>
              <div class="chip-grid">
                <span v-for="item in profile.analysis.recommendedLanguages" :key="item" class="line-chip">{{ item }}</span>
                <span v-if="!profile.analysis.recommendedLanguages.length" class="line-chip line-chip--muted">暂无</span>
              </div>
            </section>

            <section class="archive-group">
              <h4>缺失字段</h4>
              <div class="chip-grid">
                <span v-for="item in profile.analysis.missingFields" :key="item" class="line-chip line-chip--warning">{{ item }}</span>
                <span v-if="!profile.analysis.missingFields.length" class="line-chip line-chip--success">无缺口</span>
              </div>
            </section>
          </div>
        </article>

        <article class="console-panel">
          <div class="panel-head panel-head--compact">
            <h3>项目经历</h3>
            <span class="panel-meta">{{ profile.projects.length }} 项</span>
          </div>

          <div v-if="profile.projects.length" class="project-list">
            <article v-for="project in profile.projects" :key="project.projectId" class="project-card">
              <div class="project-head">
                <div>
                  <strong>{{ project.name }}</strong>
                  <p>{{ project.role || "角色待补齐" }}</p>
                </div>
                <span class="confidence-chip">{{ project.confidence }}</span>
              </div>
              <p class="project-summary">{{ project.summary || "暂无项目摘要" }}</p>
              <div class="chip-grid">
                <span v-for="tech in project.techStack" :key="tech" class="line-chip">{{ tech }}</span>
              </div>
              <ul class="line-list">
                <li v-for="item in project.achievements" :key="item">{{ item }}</li>
                <li v-if="!project.achievements.length">暂无成果记录</li>
              </ul>
            </article>
          </div>
          <p v-else class="empty-copy">暂无项目经历。</p>
        </article>

        <article class="console-panel">
          <div class="panel-head panel-head--compact">
            <h3>复核备注</h3>
            <span class="panel-meta">{{ profile.reviewNotes.length }} 条</span>
          </div>

          <ul class="line-list">
            <li v-for="note in profile.reviewNotes" :key="note">{{ note }}</li>
            <li v-if="!profile.reviewNotes.length">暂无备注</li>
          </ul>
        </article>
      </div>

      <div class="console-column">
        <article class="console-panel">
          <div class="panel-head panel-head--compact">
            <div>
              <p class="panel-kicker">风险与动作</p>
              <h3>下一步动作</h3>
            </div>
            <span class="panel-meta">{{ actionItems.length }} 条</span>
          </div>

          <div class="action-list">
            <article v-for="action in actionItems" :key="action.title" class="action-card">
              <div class="action-copy">
                <AdminToneBadge :label="action.eyebrow" :tone="action.tone" />
                <strong>{{ action.title }}</strong>
                <p>{{ action.detail }}</p>
              </div>
              <RouterLink v-if="action.to" class="inline-link" :to="action.to">{{ action.cta }}</RouterLink>
            </article>
          </div>
        </article>

        <article class="console-panel">
          <div class="panel-head panel-head--compact">
            <h3>解析风险</h3>
            <AdminToneBadge :label="`${riskItems.length} 项关注`" :tone="riskItems.length ? 'warning' : 'success'" />
          </div>

          <div v-if="riskItems.length" class="risk-list">
            <article v-for="risk in riskItems" :key="risk.label" class="risk-card">
              <div class="risk-head">
                <AdminToneBadge :label="risk.label" :tone="risk.tone" />
              </div>
              <p>{{ risk.detail }}</p>
            </article>
          </div>
          <p v-else class="empty-copy">当前解析信号稳定。</p>

          <section class="analysis-risk-block">
            <h4>分析提示</h4>
            <ul class="line-list">
              <li v-for="item in profile.analysis.risks" :key="item">{{ item }}</li>
              <li v-if="!profile.analysis.risks.length">暂无额外提示</li>
            </ul>
          </section>
        </article>

        <article class="console-panel">
          <div class="panel-head panel-head--compact">
            <h3>交付索引</h3>
            <span class="panel-meta">路由复用</span>
          </div>

          <dl class="fact-stack">
            <div class="fact-stack__row">
              <dt>考卷 ID</dt>
              <dd>{{ profile.paperId || "待生成" }}</dd>
            </div>
            <div class="fact-stack__row">
              <dt>邀请码</dt>
              <dd>{{ profile.invitationToken || "未发布" }}</dd>
            </div>
            <div class="fact-stack__row">
              <dt>结果 ID</dt>
              <dd>{{ profile.resultId || "未交卷" }}</dd>
            </div>
          </dl>
        </article>
      </div>
    </section>
  </section>

  <section v-else class="candidate-loading">
    <div class="header-eyebrow">Candidate Review</div>
    <h2 class="loading-title">{{ loadError || "正在加载候选人详情..." }}</h2>
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

type CandidateDraft = Pick<
  CandidateDetail,
  | "name"
  | "role"
  | "email"
  | "city"
  | "phone"
  | "skills"
  | "hobbies"
  | "heightCm"
  | "weightKg"
  | "availableInDays"
  | "projectSummary"
  | "reviewNotes"
>;

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
        detail: "画像已可用，直接推进发卷。",
        cta: "去发卷",
        to: paperTarget.value,
        tone: "success" as AdminTone
      };
    }

    if (key === "edit") {
      return {
        eyebrow: "建议修正",
        title: "补齐候选人画像",
        detail: "先补缺口，再推进下一步。",
        cta: "编辑画像",
        to: editTarget.value,
        tone: "warning" as AdminTone
      };
    }

    if (key === "view_result") {
      return {
        eyebrow: "已完成",
        title: "查看考试结果",
        detail: "已交卷，优先进入结果页。",
        cta: "查看结果",
        to: currentProfile.resultId ? buildResultDetailPath(currentProfile.resultId) : undefined,
        tone: "info" as AdminTone
      };
    }

    if (key === "view_entry") {
      return {
        eyebrow: "已发布",
        title: "查看考试入口状态",
        detail: "确认入口和验证码即可。",
        cta: "查看入口",
        to: paperTarget.value,
        tone: "info" as AdminTone
      };
    }

    return {
      eyebrow: "跟进提醒",
      title: "安排候选人跟进",
      detail: currentProfile.invitationToken ? "入口已生成，尽快发送并催考。" : "完成画像后及时推进。",
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
    skills: Array.isArray(draft.skills) ? draft.skills : detail.skills,
    hobbies: Array.isArray(draft.hobbies) ? draft.hobbies : detail.hobbies,
    reviewNotes: Array.isArray(draft.reviewNotes) ? draft.reviewNotes : detail.reviewNotes
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
.candidate-shell {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid #ccd8e5;
  background: #f4f8fc;
}

.console-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
  border: 1px solid #c5d4e2;
  border-left: 4px solid #1f5f99;
  background: #ffffff;
  color: #123a60;
}

.header-eyebrow,
.panel-kicker {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.header-title {
  margin: 10px 0 6px;
  font-size: 2rem;
  line-height: 1.1;
}

.header-meta,
.panel-summary,
.project-summary,
.action-card p,
.risk-card p {
  margin: 0;
  color: rgba(14, 30, 50, 0.72);
  line-height: 1.7;
}

.header-meta {
  color: #56718b;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.ghost-btn,
.primary-btn,
.inline-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 16px;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 600;
}

.ghost-btn {
  border: 1px solid #c5d4e2;
  color: #184b79;
  background: #ffffff;
}

.primary-btn {
  border: 1px solid #1f5f99;
  background: #1f5f99;
  color: #ffffff;
}

.status-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  padding: 10px 14px;
  border: 1px solid #d2dee9;
  background: #ffffff;
}

.status-note,
.skill-line,
.panel-state {
  color: #506a82;
  font-size: 0.9rem;
}

.skill-line {
  margin-left: auto;
}

.candidate-console {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.05fr) minmax(300px, 0.85fr);
  gap: 14px;
}

.console-column {
  display: grid;
  align-content: start;
  gap: 14px;
}

.console-panel {
  display: grid;
  gap: 16px;
  padding: 18px;
  border: 1px solid #d1dce7;
  background: #ffffff;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-head--compact {
  align-items: center;
}

.panel-head h2,
.panel-head h3,
.archive-group h4,
.analysis-risk-block h4 {
  margin: 0;
}

.score-box {
  display: grid;
  place-items: center;
  min-width: 70px;
  min-height: 70px;
  border: 1px solid #bfd0e1;
  background: #f7fbff;
  color: #154d80;
}

.score-box span {
  font-size: 1.55rem;
  font-weight: 700;
}

.score-box small,
.panel-meta,
.fact-item dt,
.fact-stack__row dt {
  color: #5c7289;
}

.metric-grid,
.fact-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.metric-card,
.project-card,
.action-card,
.risk-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid #dbe4ed;
  background: #fbfdff;
}

.metric-card strong {
  font-size: 1.35rem;
  color: #123d65;
}

.metric-card span {
  color: #5c7289;
}

.fact-item {
  display: grid;
  gap: 6px;
  padding: 14px;
  border: 1px solid #e1e9f0;
  background: #fbfdff;
}

.fact-item dd,
.fact-stack__row dd {
  margin: 0;
  font-weight: 600;
  color: #163b5f;
}

.archive-groups,
.project-list,
.action-list,
.risk-list {
  display: grid;
  gap: 14px;
}

.archive-group {
  display: grid;
  gap: 10px;
  padding: 14px 0;
  border-bottom: 1px solid #e5edf5;
}

.archive-group:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.line-chip,
.confidence-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid #d4e0eb;
  background: #f7fbff;
  color: #1b5a8f;
  font-size: 0.88rem;
}

.line-chip--muted {
  background: #f1f5f9;
  color: #64748b;
}

.line-chip--warning {
  background: #fff4e8;
  color: #b76b1d;
}

.line-chip--success {
  background: #ecfdf3;
  color: #1c7c4a;
}

.line-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 8px;
  color: #37536d;
}

.project-head,
.risk-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.project-head p {
  margin: 4px 0 0;
  color: #5c7289;
}

.action-copy {
  display: grid;
  gap: 8px;
}

.inline-link {
  justify-self: flex-start;
  padding: 0;
  min-height: auto;
  color: #1d64a1;
}

.analysis-risk-block {
  display: grid;
  gap: 8px;
  padding-top: 4px;
}

.fact-stack {
  margin: 0;
  display: grid;
  gap: 12px;
}

.fact-stack__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5edf5;
}

.fact-stack__row:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.empty-copy {
  margin: 0;
  color: #5c7289;
}

.candidate-loading {
  display: grid;
  gap: 8px;
  padding: 24px;
  border: 1px solid #ccd8e5;
  border-left: 4px solid #1f5f99;
  background: #ffffff;
}

.loading-title {
  margin: 0;
  color: #163b5f;
}

@media (max-width: 1180px) {
  .candidate-console {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .candidate-shell {
    padding: 16px;
  }

  .console-header,
  .panel-head,
  .panel-head--compact,
  .fact-stack__row {
    flex-direction: column;
    align-items: flex-start;
  }

  .candidate-console,
  .metric-grid,
  .fact-grid {
    grid-template-columns: 1fr;
  }

  .header-actions {
    justify-content: flex-start;
  }
}
</style>
