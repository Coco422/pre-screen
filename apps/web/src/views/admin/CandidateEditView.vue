<template>
  <section v-if="ready" class="candidate-edit-page">
    <header class="edit-page__header">
      <div class="edit-page__copy">
        <p class="edit-page__eyebrow">编辑画像</p>
        <h1 class="edit-page__title">候选人画像编辑</h1>
        <p class="edit-page__meta">{{ form.name || sourceDetail?.name || "候选人" }} · {{ form.role || "岗位待补齐" }}</p>
      </div>

      <div class="edit-page__actions">
        <RouterLink class="edit-btn edit-btn--ghost" :to="detailTarget">返回详情</RouterLink>
        <RouterLink class="edit-btn edit-btn--ghost" :to="paperTarget">去发卷</RouterLink>
        <button data-testid="save-profile" class="edit-btn edit-btn--primary" type="button" @click="saveDraft">保存画像</button>
      </div>
    </header>

    <ElAlert
      v-if="saveMessage"
      :title="saveMessage"
      :type="saveMessage.includes('本地草稿') ? 'warning' : 'success'"
      :closable="false"
      show-icon
      class="save-alert"
    />

    <div class="edit-page__layout">
      <aside class="edit-page__nav">
        <article class="nav-card">
          <p class="nav-card__eyebrow">编辑区块</p>
          <div class="nav-list">
            <a href="#basic-info" class="nav-item nav-item--active">基本信息</a>
            <a href="#skills" class="nav-item">技能标签</a>
            <a href="#summary" class="nav-item">项目摘要</a>
            <a href="#review-notes" class="nav-item">复核备注</a>
          </div>
        </article>

        <article class="nav-card">
          <div class="nav-score">
            <span>岗位匹配度</span>
            <strong>{{ currentSignal?.qualityScore ?? 0 }}%</strong>
          </div>
          <div class="nav-score__track">
            <span :style="{ width: `${currentSignal?.qualityScore ?? 0}%` }"></span>
          </div>
          <p class="nav-score__copy">{{ currentSignal?.readinessLabel ?? "等待解析结果" }}</p>
        </article>

        <article class="nav-card">
          <div class="nav-card__head">
            <span>原始信号</span>
            <span>{{ sourceDetail?.analysis.missingFields.length ?? 0 }} 项缺口</span>
          </div>
          <div class="tag-cloud">
            <span v-for="item in sourceDetail?.analysis.recommendedLanguages || []" :key="item" class="tag-chip">{{ item }}</span>
            <span v-if="!(sourceDetail?.analysis.recommendedLanguages || []).length" class="tag-chip tag-chip--muted">暂无</span>
          </div>
        </article>
      </aside>

      <section class="edit-page__content">
        <article id="basic-info" class="edit-card">
          <div class="edit-card__head">
            <div>
              <p class="edit-card__eyebrow">基本信息</p>
              <h2>联系信息与到岗信号</h2>
            </div>
            <div class="edit-card__badges">
              <ElTag effect="plain">{{ sourceDetail?.status || "待复核" }}</ElTag>
              <ElTag effect="plain" type="info">{{ sourceDetail?.quality || "待解析" }}</ElTag>
            </div>
          </div>

          <div class="field-grid">
            <label class="field">
              <span>姓名</span>
              <input v-model="form.name" name="name" class="field-input" />
            </label>
            <label class="field">
              <span>岗位</span>
              <input v-model="form.role" name="role" class="field-input" />
            </label>
            <label class="field">
              <span>邮箱</span>
              <input v-model="form.email" name="email" class="field-input" />
            </label>
            <label class="field">
              <span>城市</span>
              <input v-model="form.city" name="city" class="field-input" />
            </label>
            <label class="field">
              <span>电话</span>
              <input v-model="form.phone" name="phone" class="field-input" />
            </label>
            <label class="field">
              <span>可到岗天数</span>
              <input v-model="form.availableInDaysText" name="availableInDaysText" class="field-input" />
            </label>
            <label class="field">
              <span>身高（cm）</span>
              <input v-model="form.heightCmText" name="heightCmText" class="field-input" />
            </label>
            <label class="field">
              <span>体重（kg）</span>
              <input v-model="form.weightKgText" name="weightKgText" class="field-input" />
            </label>
          </div>
        </article>

        <article id="skills" class="edit-card">
          <div class="edit-card__head">
            <div>
              <p class="edit-card__eyebrow">结构化档案</p>
              <h2>技能标签与兴趣标签</h2>
            </div>
            <span class="edit-card__meta">标签化输入</span>
          </div>

          <div class="field-grid field-grid--single">
            <label class="field field--full">
              <span>技能标签（逗号分隔）</span>
              <input v-model="form.skillsText" name="skillsText" class="field-input" />
            </label>
            <div class="preview-block">
              <span class="preview-block__label">技能预览</span>
              <div class="tag-cloud">
                <span v-for="item in skillPreview" :key="item" class="tag-chip">{{ item }}</span>
                <span v-if="!skillPreview.length" class="tag-chip tag-chip--muted">暂无</span>
              </div>
            </div>

            <label class="field field--full">
              <span>爱好标签（逗号分隔）</span>
              <input v-model="form.hobbiesText" name="hobbiesText" class="field-input" />
            </label>
            <div class="preview-block">
              <span class="preview-block__label">兴趣预览</span>
              <div class="tag-cloud">
                <span v-for="item in hobbyPreview" :key="item" class="tag-chip tag-chip--light">{{ item }}</span>
                <span v-if="!hobbyPreview.length" class="tag-chip tag-chip--muted">暂无</span>
              </div>
            </div>
          </div>
        </article>

        <article id="summary" class="edit-card">
          <div class="edit-card__head">
            <div>
              <p class="edit-card__eyebrow">岗位匹配</p>
              <h2>项目摘要与推荐信号</h2>
            </div>
            <span class="edit-card__meta">{{ currentSignal?.qualityLabel || "待解析" }}</span>
          </div>

          <div class="match-panel">
            <div class="nav-score">
              <span>岗位匹配度</span>
              <strong>{{ currentSignal?.qualityScore ?? 0 }}%</strong>
            </div>
            <div class="nav-score__track">
              <span :style="{ width: `${currentSignal?.qualityScore ?? 0}%` }"></span>
            </div>
            <p class="nav-score__copy">{{ currentSignal?.readinessLabel ?? "等待解析结果" }}</p>
          </div>

          <label class="field field--full">
            <span>项目摘要</span>
            <textarea v-model="form.projectSummary" name="projectSummary" class="field-input field-textarea" rows="7" />
          </label>

          <div class="signal-grid">
            <section class="signal-card">
              <h3>缺失字段</h3>
              <div class="tag-cloud">
                <span v-for="item in sourceDetail?.analysis.missingFields || []" :key="item" class="tag-chip tag-chip--warning">{{ item }}</span>
                <span v-if="!(sourceDetail?.analysis.missingFields || []).length" class="tag-chip tag-chip--success">无缺口</span>
              </div>
            </section>

            <section class="signal-card">
              <h3>关注主题</h3>
              <ul class="signal-list">
                <li v-for="item in sourceDetail?.analysis.focusTopics || []" :key="item">{{ item }}</li>
                <li v-if="!(sourceDetail?.analysis.focusTopics || []).length">暂无</li>
              </ul>
            </section>
          </div>
        </article>

        <article id="review-notes" class="edit-card">
          <div class="edit-card__head">
            <div>
              <p class="edit-card__eyebrow">复核备注</p>
              <h2>人工修订记录</h2>
            </div>
            <span class="edit-card__meta">每行一条</span>
          </div>

          <label class="field field--full">
            <span>复核备注</span>
            <textarea
              v-model="form.reviewNotesText"
              name="reviewNotesText"
              class="field-input field-textarea field-textarea--tall"
              rows="8"
            />
          </label>

          <section class="project-index">
            <div class="project-index__head">
              <h3>项目索引</h3>
              <span>{{ sourceDetail?.projects.length || 0 }} 项</span>
            </div>
            <div v-if="sourceDetail?.projects.length" class="project-index__list">
              <article v-for="project in sourceDetail.projects" :key="project.projectId" class="project-index__item">
                <strong>{{ project.name }}</strong>
                <p>{{ project.summary || "暂无项目摘要" }}</p>
              </article>
            </div>
            <p v-else class="empty-copy">暂无项目经历。</p>
          </section>
        </article>

        <footer class="edit-page__footer">
          <RouterLink class="edit-btn edit-btn--ghost" :to="detailTarget">取消</RouterLink>
          <button class="edit-btn edit-btn--light" type="button" @click="resetDraft">撤销本地暂存</button>
          <button class="edit-btn edit-btn--primary" type="button" @click="saveDraft">保存</button>
        </footer>
      </section>
    </div>
  </section>

  <section v-else class="edit-loading">
    <div class="edit-page__eyebrow">编辑画像</div>
    <h2 class="edit-page__title">{{ loadError || "正在加载候选人画像..." }}</h2>
  </section>
</template>

<script setup lang="ts">
import { ElAlert, ElTag } from "element-plus";
import { computed, reactive, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import {
  buildCandidateDetailPath,
  buildPaperEditorPath,
  buildPaperRouteTarget
} from "../../components/admin/adminRouting";
import { buildCandidateSignal } from "../../components/admin/adminUi";
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

type CandidateDetailResponse = {
  id: string;
  task_id: string;
  name: string;
  role: string;
  email: string;
  city: string;
  phone?: string;
  status?: string;
  quality?: string;
  skills: string[];
  hobbies?: string[];
  height_cm?: number | null;
  weight_kg?: number | null;
  available_in_days?: number | null;
  project_summary: string;
  projects?: Array<{
    project_id: string;
    name: string;
    role?: string;
    summary?: string;
    tech_stack?: string[];
    responsibilities?: string[];
    achievements?: string[];
    metrics?: string[];
    source_pages?: number[];
    confidence?: string;
  }>;
  analysis?: {
    focus_topics?: string[];
    strengths?: string[];
    risks?: string[];
    recommended_languages?: string[];
    missing_fields?: string[];
  };
  processing?: {
    stage?: string;
    status?: string;
    progress?: number;
    message?: string;
    error_message?: string | null;
    steps?: Record<string, { label?: string; status?: string }>;
  } | null;
  review_notes: string[];
  parse_metrics: {
    first_page_characters: number;
    multimodal_pages: number;
    confidence: string;
  };
  next_actions?: Array<{ label?: string; target?: string }>;
  paper_id?: string | null;
  invitation_token?: string | null;
  result_id?: string | null;
};

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";

const route = useRoute();
const ready = ref(false);
const saveMessage = ref("");
const loadError = ref("");
const sourceDetail = ref<CandidateDetail | null>(null);
let latestRequestId = 0;

const form = reactive({
  name: "",
  role: "",
  email: "",
  city: "",
  phone: "",
  skillsText: "",
  hobbiesText: "",
  heightCmText: "",
  weightKgText: "",
  availableInDaysText: "",
  projectSummary: "",
  reviewNotesText: ""
});

const candidateId = computed(() => (typeof route.params.candidateId === "string" ? route.params.candidateId : ""));
const detailTarget = computed(() => buildCandidateDetailPath(candidateId.value));
const paperTarget = computed(() => ({
  ...buildPaperRouteTarget(candidateId.value),
  path: buildPaperEditorPath(sourceDetail.value?.paperId),
  query: {
    candidateId: candidateId.value,
    candidateName: form.name
  }
}));
const currentSignal = computed(() => (sourceDetail.value ? buildCandidateSignal(sourceDetail.value) : null));
const skillPreview = computed(() =>
  form.skillsText
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
);
const hobbyPreview = computed(() =>
  form.hobbiesText
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
);

function readDraft(targetCandidateId: string): Partial<CandidateDraft> | null {
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

function clearDraft(targetCandidateId: string) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(`admin-candidate-draft:${targetCandidateId}`);
}

function mapProcessingStatus(input?: CandidateDetailResponse["processing"]): CandidateDetail["processing"] {
  if (!input) {
    return null;
  }

  const steps = Object.fromEntries(
    Object.entries(input.steps ?? {}).map(([key, item]) => [
      key,
      {
        label: item.label ?? key,
        status: item.status ?? "pending"
      }
    ])
  );

  return {
    stage: input.stage ?? "unknown",
    status: input.status ?? "unknown",
    progress: input.progress ?? 0,
    message: input.message ?? "",
    errorMessage: input.error_message,
    steps
  };
}

function mapCandidateDetailResponse(response: CandidateDetailResponse): CandidateDetail {
  const derivedPaperId =
    response.paper_id ??
    response.next_actions?.find((item) => item.target?.includes("/admin/papers/"))?.target?.match(/\/admin\/papers\/([^/?#]+)/)?.[1] ??
    null;

  return {
    id: response.id,
    taskId: response.task_id,
    name: response.name,
    role: response.role,
    email: response.email,
    city: response.city,
    phone: response.phone ?? "",
    status: response.status ?? "待审核",
    quality: response.quality ?? response.parse_metrics.confidence,
    skills: response.skills,
    hobbies: response.hobbies ?? [],
    heightCm: response.height_cm,
    weightKg: response.weight_kg,
    availableInDays: response.available_in_days,
    projectSummary: response.project_summary,
    projects: (response.projects ?? []).map((project) => ({
      projectId: project.project_id,
      name: project.name,
      role: project.role ?? "",
      summary: project.summary ?? "",
      techStack: project.tech_stack ?? [],
      responsibilities: project.responsibilities ?? [],
      achievements: project.achievements ?? [],
      metrics: project.metrics ?? [],
      sourcePages: project.source_pages ?? [],
      confidence: project.confidence ?? "medium"
    })),
    analysis: {
      focusTopics: response.analysis?.focus_topics ?? [],
      strengths: response.analysis?.strengths ?? [],
      risks: response.analysis?.risks ?? [],
      recommendedLanguages: response.analysis?.recommended_languages ?? [],
      missingFields: response.analysis?.missing_fields ?? []
    },
    processing: mapProcessingStatus(response.processing),
    reviewNotes: response.review_notes,
    parseMetrics: {
      firstPageCharacters: response.parse_metrics.first_page_characters,
      multimodalPages: response.parse_metrics.multimodal_pages,
      confidence: response.parse_metrics.confidence
    },
    paperId: derivedPaperId,
    invitationToken: response.invitation_token,
    resultId: response.result_id
  };
}

async function submitCandidateDetailUpdate(targetCandidateId: string, payload: CandidateDraft): Promise<CandidateDetail> {
  const response = await fetch(`${API_BASE}/admin/candidates/${targetCandidateId}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      name: payload.name,
      role: payload.role,
      email: payload.email,
      city: payload.city,
      phone: payload.phone,
      skills: payload.skills,
      hobbies: payload.hobbies,
      height_cm: payload.heightCm,
      weight_kg: payload.weightKg,
      available_in_days: payload.availableInDays,
      project_summary: payload.projectSummary,
      review_notes: payload.reviewNotes
    })
  });

  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }

  return mapCandidateDetailResponse((await response.json()) as CandidateDetailResponse);
}

function applyToForm(detail: CandidateDetail, draft: Partial<CandidateDraft> | null) {
  const merged = {
    ...detail,
    ...draft,
    skills: Array.isArray(draft?.skills) ? draft.skills : detail.skills,
    hobbies: Array.isArray(draft?.hobbies) ? draft.hobbies : detail.hobbies,
    reviewNotes: Array.isArray(draft?.reviewNotes) ? draft.reviewNotes : detail.reviewNotes
  };

  form.name = merged.name;
  form.role = merged.role;
  form.email = merged.email;
  form.city = merged.city;
  form.phone = merged.phone;
  form.skillsText = merged.skills.join(", ");
  form.hobbiesText = merged.hobbies.join(", ");
  form.heightCmText = merged.heightCm == null ? "" : String(merged.heightCm);
  form.weightKgText = merged.weightKg == null ? "" : String(merged.weightKg);
  form.availableInDaysText = merged.availableInDays == null ? "" : String(merged.availableInDays);
  form.projectSummary = merged.projectSummary;
  form.reviewNotesText = merged.reviewNotes.join("\n");
}

function parseOptionalNumber(value: string) {
  if (!value.trim()) {
    return null;
  }

  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function buildDraftPayload(): CandidateDraft {
  return {
    name: form.name.trim(),
    role: form.role.trim(),
    email: form.email.trim(),
    city: form.city.trim(),
    phone: form.phone.trim(),
    skills: form.skillsText
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    hobbies: form.hobbiesText
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean),
    heightCm: parseOptionalNumber(form.heightCmText),
    weightKg: parseOptionalNumber(form.weightKgText),
    availableInDays: parseOptionalNumber(form.availableInDaysText),
    projectSummary: form.projectSummary.trim(),
    reviewNotes: form.reviewNotesText
      .split("\n")
      .map((item) => item.trim())
      .filter(Boolean)
  };
}

async function saveDraft() {
  if (!candidateId.value) {
    return;
  }

  const submitCandidateId = candidateId.value;
  const submitRequestId = latestRequestId;
  const payload = buildDraftPayload();

  try {
    const detail = await submitCandidateDetailUpdate(submitCandidateId, payload);
    if (submitCandidateId !== candidateId.value || submitRequestId !== latestRequestId) {
      return;
    }

    sourceDetail.value = detail;
    clearDraft(submitCandidateId);
    applyToForm(detail, null);
    saveMessage.value = "画像已同步到后端。";
  } catch {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(`admin-candidate-draft:${submitCandidateId}`, JSON.stringify(payload));
    }

    if (submitCandidateId !== candidateId.value || submitRequestId !== latestRequestId) {
      return;
    }

    saveMessage.value = "本地草稿已保存。";
  }
}

function resetDraft() {
  if (!candidateId.value || !sourceDetail.value) {
    return;
  }

  clearDraft(candidateId.value);
  applyToForm(sourceDetail.value, null);
  saveMessage.value = "已撤销本地暂存，恢复为当前详情数据。";
}

watch(
  candidateId,
  async (nextCandidateId) => {
    if (!nextCandidateId) {
      ready.value = false;
      sourceDetail.value = null;
      return;
    }

    const requestId = ++latestRequestId;
    ready.value = false;
    saveMessage.value = "";
    loadError.value = "";

    try {
      const detail = await loadCandidateDetail(nextCandidateId);
      if (requestId !== latestRequestId) {
        return;
      }

      sourceDetail.value = detail;
      applyToForm(detail, readDraft(nextCandidateId));
      ready.value = true;
    } catch {
      if (requestId !== latestRequestId) {
        return;
      }

      loadError.value = "候选人画像加载失败，请稍后重试。";
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.candidate-edit-page {
  display: grid;
  gap: 14px;
  min-height: 100%;
  padding: 16px 18px 18px;
  border: 1px solid #d7e1ee;
  border-radius: 14px;
  background: linear-gradient(180deg, #f7fbff 0%, #f3f7fd 100%), #f7fbff;
}

.edit-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  padding: 4px 2px 10px;
  border-bottom: 1px solid #dde7f2;
}

.edit-page__copy {
  display: grid;
  gap: 6px;
}

.edit-page__eyebrow,
.edit-card__eyebrow,
.nav-card__eyebrow {
  margin: 0;
  color: #5d7596;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.edit-page__title {
  margin: 0;
  color: #1a2a41;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.1;
}

.edit-page__meta,
.nav-score__copy,
.preview-block__label,
.edit-card__meta,
.empty-copy,
.project-index__item p {
  margin: 0;
  color: #58708f;
  line-height: 1.6;
}

.edit-page__actions,
.edit-page__footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.edit-btn {
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

.edit-btn--primary {
  border-color: #2f6cf6;
  background: linear-gradient(180deg, #4384ff 0%, #2f6cf6 100%);
  color: #ffffff;
}

.edit-btn--light {
  background: #f5f9ff;
}

.save-alert {
  border-radius: 12px;
}

.edit-page__layout {
  display: grid;
  grid-template-columns: minmax(220px, 0.34fr) minmax(0, 1fr);
  gap: 14px;
}

.edit-page__nav,
.edit-page__content {
  display: grid;
  align-content: start;
  gap: 14px;
}

.nav-card,
.edit-card {
  display: grid;
  gap: 16px;
  padding: 18px;
  border: 1px solid #d6e0ec;
  border-radius: 12px;
  background: #ffffff;
}

.nav-list {
  display: grid;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  min-height: 36px;
  padding: 0 12px;
  border: 1px solid #e2eaf3;
  border-radius: 10px;
  color: #4f6786;
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
}

.nav-item--active {
  border-color: #cfe0ff;
  background: #f5f9ff;
  color: #2f6cf6;
}

.nav-score {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  color: #223550;
}

.nav-score strong {
  color: #2f6cf6;
  font-size: 20px;
}

.nav-score__track {
  overflow: hidden;
  height: 8px;
  border-radius: 999px;
  background: #e7eef8;
}

.nav-score__track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #5d8ef0 0%, #2f69d9 100%);
}

.nav-card__head,
.project-index__head,
.edit-card__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.edit-card__head h2,
.project-index__head h3,
.signal-card h3 {
  margin: 0;
  color: #1a2a41;
}

.edit-card__badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field-grid--single {
  grid-template-columns: 1fr;
}

.field {
  display: grid;
  gap: 8px;
}

.field span {
  color: #5d7596;
}

.field--full {
  grid-column: 1 / -1;
}

.field-input {
  width: 100%;
  min-height: 44px;
  padding: 10px 14px;
  border: 1px solid #c9d9ea;
  border-radius: 10px;
  background: #fbfdff;
  color: #163b5f;
  font: inherit;
  box-sizing: border-box;
}

.field-input:focus {
  outline: none;
  border-color: #5f96c8;
  box-shadow: 0 0 0 3px rgba(95, 150, 200, 0.15);
}

.field-textarea {
  resize: vertical;
  min-height: 160px;
}

.field-textarea--tall {
  min-height: 220px;
}

.preview-block,
.project-index,
.match-panel {
  display: grid;
  gap: 10px;
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

.tag-chip--warning {
  border-color: #f2d8ac;
  background: #fff9ef;
  color: #b06b00;
}

.tag-chip--success {
  border-color: #cfe4d3;
  background: #f4fbf6;
  color: #2d7a49;
}

.tag-chip--muted {
  color: #6b7f98;
}

.signal-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.signal-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid #e3ebf4;
  border-radius: 10px;
  background: #fbfdff;
}

.signal-list {
  display: grid;
  gap: 8px;
  margin: 0;
  padding-left: 18px;
  color: #253852;
}

.project-index__head span {
  color: #617793;
  font-size: 13px;
}

.project-index__list {
  display: grid;
  gap: 10px;
}

.project-index__item {
  display: grid;
  gap: 6px;
  padding: 12px 14px;
  border: 1px solid #e5ecf5;
  border-radius: 10px;
  background: #fbfdff;
}

.project-index__item strong {
  color: #1d2d43;
}

.edit-page__footer {
  justify-content: flex-end;
}

.edit-loading {
  display: grid;
  gap: 10px;
  padding: 40px 24px;
  border: 1px solid #d7e1ee;
  border-radius: 14px;
  background: #f4f7fb;
}

@media (max-width: 1200px) {
  .edit-page__layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .candidate-edit-page {
    padding: 14px;
  }

  .edit-page__header {
    flex-direction: column;
  }

  .field-grid,
  .signal-grid {
    grid-template-columns: 1fr;
  }

  .edit-page__actions,
  .edit-page__footer {
    width: 100%;
  }

  .edit-btn {
    width: 100%;
  }
}
</style>
