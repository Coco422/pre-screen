<template>
  <section v-if="profile" class="candidate-detail-page">
    <header class="detail-page__header">
      <div class="detail-page__copy">
        <p class="detail-page__eyebrow">候选人详情</p>
        <h1 class="detail-page__title">{{ profile.name }}</h1>
        <p class="detail-page__meta">{{ profile.role }} · {{ profile.city || "城市待补齐" }} · {{ profile.status }}</p>
      </div>

      <div class="detail-page__actions">
        <RouterLink class="detail-btn detail-btn--ghost" :to="{ name: 'admin-candidates' }">返回列表</RouterLink>
        <RouterLink class="detail-btn detail-btn--ghost" :to="editTarget">编辑画像</RouterLink>
        <RouterLink class="detail-btn detail-btn--primary" :to="paperTarget">去发卷</RouterLink>
      </div>
    </header>

    <div class="detail-page__status">
      <AdminToneBadge :label="profile.status" :tone="statusTone" />
      <AdminToneBadge :label="`解析质量 ${profile.quality}`" :tone="signal.tone" />
      <AdminToneBadge :label="signal.readinessLabel" :tone="signal.tone" />
      <span class="detail-page__status-note">{{ projectSummaryState.label }}</span>
    </div>

    <section class="review-board">
      <article class="review-panel">
        <div class="review-panel__head">
          <div>
            <p class="review-panel__eyebrow">基本信息</p>
            <h2>候选人档案</h2>
          </div>
        </div>

        <div class="identity-card">
          <div class="identity-card__avatar">{{ profile.name.slice(-1) || "人" }}</div>
          <div class="identity-card__copy">
            <strong>{{ profile.name }}</strong>
            <span>{{ profile.role }}</span>
            <div class="identity-card__meta">
              <span>{{ profile.city || "城市待补齐" }}</span>
              <span>{{ profile.availableInDays == null ? "到岗待确认" : `${profile.availableInDays} 天可到岗` }}</span>
              <span>{{ signal.qualityLabel }}</span>
            </div>
          </div>
        </div>

        <dl class="info-grid">
          <div class="info-grid__item">
            <dt>手机号</dt>
            <dd>{{ profile.phone || "待补齐" }}</dd>
          </div>
          <div class="info-grid__item">
            <dt>邮箱</dt>
            <dd>{{ profile.email || "待补齐" }}</dd>
          </div>
          <div class="info-grid__item">
            <dt>首页字符</dt>
            <dd>{{ profile.parseMetrics.firstPageCharacters }}</dd>
          </div>
          <div class="info-grid__item">
            <dt>补读页数</dt>
            <dd>{{ profile.parseMetrics.multimodalPages }}</dd>
          </div>
        </dl>

        <section class="resume-card">
          <div>
            <p class="resume-card__label">简历文件</p>
            <strong>{{ profile.name }}_简历.pdf</strong>
            <span>{{ profile.quality }}质量 · {{ profile.parseMetrics.confidence }}置信度</span>
          </div>
          <RouterLink class="detail-inline-link" :to="editTarget">查看编辑稿</RouterLink>
        </section>

        <section class="notes-block">
          <div class="notes-block__head">
            <h3>复核备注</h3>
            <span>{{ profile.reviewNotes.length }} 条</span>
          </div>
          <ul class="notes-list">
            <li v-for="note in profile.reviewNotes" :key="note">{{ note }}</li>
            <li v-if="!profile.reviewNotes.length">暂无备注</li>
          </ul>
        </section>
      </article>

      <article class="review-panel">
        <div class="review-panel__head">
          <div>
            <p class="review-panel__eyebrow">结构化档案</p>
            <h2>岗位匹配画像</h2>
          </div>
          <span class="review-panel__meta">{{ profile.analysis.missingFields.length ? "待补字段" : "字段齐全" }}</span>
        </div>

        <section class="archive-block">
          <h3>技能标签</h3>
          <div class="tag-cloud">
            <span v-for="skill in profile.skills" :key="skill" class="tag-chip">{{ skill }}</span>
            <span v-if="!profile.skills.length" class="tag-chip tag-chip--muted">暂无</span>
          </div>
        </section>

        <section class="archive-block">
          <h3>关注主题</h3>
          <div class="tag-cloud">
            <span v-for="item in profile.analysis.focusTopics" :key="item" class="tag-chip">{{ item }}</span>
            <span v-if="!profile.analysis.focusTopics.length" class="tag-chip tag-chip--muted">暂无</span>
          </div>
        </section>

        <section class="archive-block">
          <h3>项目经历</h3>
          <div v-if="profile.projects.length" class="project-timeline">
            <article v-for="project in profile.projects" :key="project.projectId" class="project-entry">
              <div class="project-entry__head">
                <strong>{{ project.name }}</strong>
                <span>{{ project.role || "角色待补齐" }}</span>
              </div>
              <p>{{ project.summary || "暂无项目摘要" }}</p>
              <div class="tag-cloud">
                <span v-for="tech in project.techStack" :key="tech" class="tag-chip tag-chip--light">{{ tech }}</span>
              </div>
            </article>
          </div>
          <p v-else class="empty-copy">暂无项目经历。</p>
        </section>

        <section class="archive-block">
          <h3>岗位匹配度</h3>
          <AdminScoreBar
            label="岗位匹配度"
            :value="signal.qualityScore"
            :percent="signal.qualityScore"
            :detail="signal.readinessLabel"
            :tone="signal.tone"
          />
          <p class="archive-block__summary">{{ profile.projectSummary }}</p>
        </section>
      </article>

      <article class="review-panel">
        <div class="review-panel__head">
          <div>
            <p class="review-panel__eyebrow">风险与操作</p>
            <h2>推进动作</h2>
          </div>
          <span class="review-panel__meta">{{ riskItems.length }} 项关注</span>
        </div>

        <section class="risk-block">
          <div class="risk-block__head">
            <h3>风险提示</h3>
            <span>{{ riskItems.length }} 条</span>
          </div>
          <ul v-if="riskItems.length" class="risk-list">
            <li v-for="risk in riskItems" :key="risk.label">
              <AdminToneBadge :label="risk.label" :tone="risk.tone" />
              <p>{{ risk.detail }}</p>
            </li>
          </ul>
          <p v-else class="empty-copy">当前解析信号稳定。</p>
        </section>

        <section class="risk-block">
          <div class="risk-block__head">
            <h3>分析提示</h3>
            <span>{{ profile.analysis.risks.length }} 条</span>
          </div>
          <ul class="notes-list">
            <li v-for="item in profile.analysis.risks" :key="item">{{ item }}</li>
            <li v-if="!profile.analysis.risks.length">暂无额外提示</li>
          </ul>
        </section>

        <section class="action-block">
          <h3>操作</h3>
          <div class="action-block__buttons">
            <RouterLink class="detail-btn detail-btn--ghost" :to="editTarget">编辑画像</RouterLink>
            <RouterLink class="detail-btn detail-btn--ghost" :to="paperTarget">
              {{ profile.paperId ? "查看考卷" : "生成考卷" }}
            </RouterLink>
            <RouterLink class="detail-btn detail-btn--primary" :to="paperTarget">
              {{ profile.invitationToken ? "查看入口" : "发卷" }}
            </RouterLink>
            <button class="detail-btn detail-btn--danger" type="button">淘汰</button>
          </div>
        </section>

        <section class="delivery-block">
          <h3>交付索引</h3>
          <dl class="delivery-grid">
            <div>
              <dt>考卷 ID</dt>
              <dd>{{ profile.paperId || "待生成" }}</dd>
            </div>
            <div>
              <dt>邀请码</dt>
              <dd>{{ profile.invitationToken || "未发布" }}</dd>
            </div>
            <div>
              <dt>结果 ID</dt>
              <dd>{{ profile.resultId || "未交卷" }}</dd>
            </div>
          </dl>
        </section>

        <section class="resume-pdf-block">
          <h3>简历原件</h3>
          <div v-if="profile.resumePdfUrl" class="pdf-viewer">
            <VuePdfEmbed :source="pdfSource" class="pdf-embed" />
          </div>
          <p v-else class="empty-copy">暂无 PDF 原件</p>
        </section>
      </article>
    </section>
  </section>

  <section v-else class="candidate-loading">
    <div class="detail-page__eyebrow">候选人详情</div>
    <h2 class="loading-title">{{ loadError || "正在加载候选人详情..." }}</h2>
  </section>
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AdminScoreBar from "../../components/admin/AdminScoreBar.vue";
import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import {
  buildCandidateEditPath,
  buildPaperEditorPath,
  buildPaperRouteTarget
} from "../../components/admin/adminRouting";
import {
  buildCandidateRiskItems,
  buildCandidateSignal,
  type AdminTone
} from "../../components/admin/adminUi";
import { loadCandidateDetail, type CandidateDetail } from "../../lib/gateway";

const VuePdfEmbed = defineAsyncComponent(() => import("vue-pdf-embed"));

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

const pdfSource = computed(() => {
  if (!profile.value?.resumePdfUrl) {
    return "";
  }
  const url = profile.value.resumePdfUrl;
  if (url.startsWith("http://") || url.startsWith("https://") || url.startsWith("data:")) {
    return url;
  }
  return `/api${url}`;
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
.candidate-detail-page {
  display: grid;
  gap: 14px;
  min-height: 100%;
  padding: 16px 18px 18px;
  border: 1px solid #d7e1ee;
  border-radius: 14px;
  background: linear-gradient(180deg, #f7fbff 0%, #f3f7fd 100%), #f7fbff;
}

.detail-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 4px 2px 10px;
  border-bottom: 1px solid #dde7f2;
}

.detail-page__copy {
  display: grid;
  gap: 6px;
}

.detail-page__eyebrow,
.review-panel__eyebrow {
  margin: 0;
  color: #5d7596;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.detail-page__title {
  margin: 0;
  color: #1a2a41;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.1;
}

.detail-page__meta,
.archive-block__summary,
.project-entry p,
.risk-list p,
.empty-copy {
  margin: 0;
  color: #58708f;
  line-height: 1.6;
}

.detail-page__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.detail-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0 16px;
  border: 1px solid #d3deeb;
  border-radius: 10px;
  background: #ffffff;
  color: #245389;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.detail-btn--primary {
  border-color: #2f6cf6;
  background: linear-gradient(180deg, #4384ff 0%, #2f6cf6 100%);
  color: #ffffff;
}

.detail-btn--danger {
  border-color: #f3c5c1;
  color: #d34f45;
  background: #fff8f7;
}

.detail-page__status {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.detail-page__status-note,
.review-panel__meta,
.notes-block__head span,
.risk-block__head span {
  color: #617793;
  font-size: 13px;
}

.review-board {
  display: grid;
  grid-template-columns: minmax(280px, 0.92fr) minmax(360px, 1.14fr) minmax(280px, 0.88fr);
  gap: 14px;
}

.review-panel {
  display: grid;
  align-content: start;
  gap: 16px;
  padding: 18px;
  border: 1px solid #d6e0ec;
  border-radius: 12px;
  background: #ffffff;
}

.review-panel__head,
.notes-block__head,
.risk-block__head,
.project-entry__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.review-panel__head h2,
.review-panel__head h3,
.notes-block__head h3,
.risk-block__head h3,
.delivery-block h3,
.archive-block h3 {
  margin: 0;
  color: #1a2a41;
}

.identity-card {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr);
  gap: 14px;
  align-items: center;
  padding: 16px;
  border: 1px solid #dce6f2;
  border-radius: 12px;
  background: linear-gradient(180deg, #fbfdff 0%, #f5f9ff 100%);
}

.identity-card__avatar {
  display: grid;
  place-items: center;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(180deg, #d8e8ff 0%, #c6dafd 100%);
  color: #1e58a5;
  font-size: 26px;
  font-weight: 700;
}

.identity-card__copy {
  display: grid;
  gap: 4px;
}

.identity-card__copy strong {
  color: #1d2d43;
  font-size: 18px;
}

.identity-card__copy span {
  color: #5f7593;
}

.identity-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  margin-top: 2px;
  font-size: 13px;
}

.info-grid,
.delivery-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.info-grid__item,
.delivery-grid div {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid #e3ebf4;
  border-radius: 10px;
  background: #fbfdff;
}

.info-grid__item dt,
.delivery-grid dt {
  color: #6b7f98;
  font-size: 12px;
}

.info-grid__item dd,
.delivery-grid dd {
  margin: 0;
  color: #21344f;
  font-weight: 600;
}

.resume-card,
.notes-block,
.risk-block,
.delivery-block,
.archive-block {
  display: grid;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid #e8eef5;
}

.resume-card {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.resume-card__label {
  margin: 0 0 6px;
  color: #6b7f98;
  font-size: 12px;
}

.resume-card strong,
.resume-card span {
  display: block;
}

.resume-card span {
  margin-top: 4px;
  color: #5f7593;
  font-size: 13px;
}

.detail-inline-link {
  color: #2f6cf6;
  text-decoration: none;
  font-size: 13px;
  font-weight: 600;
}

.notes-list,
.risk-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding-left: 18px;
  color: #253852;
}

.risk-list {
  padding-left: 0;
  list-style: none;
}

.risk-list li {
  display: grid;
  gap: 8px;
  padding: 12px;
  border: 1px solid #e5ecf5;
  border-radius: 10px;
  background: #fbfdff;
}

.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border: 1px solid #d7e4f3;
  border-radius: 8px;
  background: #f5f9ff;
  color: #2a65b8;
  font-size: 13px;
}

.tag-chip--light {
  background: #ffffff;
  color: #51739e;
}

.tag-chip--muted {
  color: #6b7f98;
}

.project-timeline {
  display: grid;
  gap: 12px;
}

.project-entry {
  display: grid;
  gap: 8px;
  padding-left: 14px;
  border-left: 2px solid #dce6f5;
}

.project-entry__head strong {
  color: #1d2d43;
}

.action-block {
  display: grid;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid #e8eef5;
}

.action-block__buttons {
  display: grid;
  gap: 10px;
}

.candidate-loading {
  display: grid;
  gap: 10px;
  padding: 40px 24px;
  border: 1px solid #d7e1ee;
  border-radius: 14px;
  background: #f4f7fb;
}

.loading-title {
  margin: 0;
  color: #1d2d43;
}

@media (max-width: 1280px) {
  .review-board {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .candidate-detail-page {
    padding: 14px;
  }

  .detail-page__header {
    flex-direction: column;
  }

  .detail-page__actions,
  .resume-card {
    grid-template-columns: 1fr;
  }

  .detail-btn {
    width: 100%;
  }

  .info-grid,
  .delivery-grid {
    grid-template-columns: 1fr;
  }
}

.resume-pdf-block {
  margin-top: 18px;
}

.resume-pdf-block h3 {
  margin: 0 0 12px;
  font-size: 13px;
  font-weight: 600;
  color: #3a5070;
}

.pdf-viewer {
  min-height: 400px;
  max-height: 700px;
  overflow: auto;
  border-radius: 10px;
  border: 1px solid #dde7f2;
  background: #f8fafc;
}

.pdf-embed {
  width: 100%;
}
</style>
