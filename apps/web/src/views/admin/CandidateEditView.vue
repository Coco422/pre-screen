<template>
  <section v-if="ready" class="edit-shell">
    <header class="workspace-header">
      <div class="workspace-copy">
        <div class="workspace-eyebrow">Profile Edit</div>
        <h1 class="workspace-title">编辑候选人画像</h1>
        <p class="workspace-meta">{{ form.name || sourceDetail?.name || "候选人" }} · {{ form.role || "岗位待补齐" }}</p>
      </div>

      <div class="workspace-actions">
        <RouterLink class="ghost-btn" :to="detailTarget">返回详情</RouterLink>
        <RouterLink class="ghost-btn" :to="paperTarget">去发卷</RouterLink>
        <button data-testid="save-profile" class="primary-btn" type="button" @click="saveDraft">保存画像</button>
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

    <section class="edit-workspace">
      <div class="workspace-main">
        <article class="workspace-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">基础资料</p>
              <h2>联系信息与到岗信号</h2>
            </div>
            <div class="panel-badges">
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

        <article class="workspace-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">结构画像</p>
              <h2>标签、兴趣与项目摘要</h2>
            </div>
            <span class="panel-meta">结构字段</span>
          </div>

          <div class="field-grid field-grid--wide">
            <label class="field field--full">
              <span>技能标签（逗号分隔）</span>
              <input v-model="form.skillsText" name="skillsText" class="field-input" />
            </label>
            <label class="field field--full">
              <span>爱好标签（逗号分隔）</span>
              <input v-model="form.hobbiesText" name="hobbiesText" class="field-input" />
            </label>
            <label class="field field--full">
              <span>项目摘要</span>
              <textarea v-model="form.projectSummary" name="projectSummary" class="field-input field-textarea" rows="6" />
            </label>
          </div>
        </article>

        <article class="workspace-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">复核备注</p>
              <h2>人工修订记录</h2>
            </div>
            <span class="panel-meta">每行一条</span>
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
        </article>
      </div>

      <aside class="workspace-sidebar">
        <article class="workspace-panel sidebar-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">当前信号</p>
              <h3>解析侧栏</h3>
            </div>
          </div>

          <section class="sidebar-block">
            <h4>推荐语言</h4>
            <div class="chip-grid">
              <span v-for="item in sourceDetail?.analysis.recommendedLanguages || []" :key="item" class="line-chip">{{ item }}</span>
              <span v-if="!(sourceDetail?.analysis.recommendedLanguages || []).length" class="line-chip line-chip--muted">暂无</span>
            </div>
          </section>

          <section class="sidebar-block">
            <h4>缺失字段</h4>
            <div class="chip-grid">
              <span v-for="item in sourceDetail?.analysis.missingFields || []" :key="item" class="line-chip line-chip--warning">{{ item }}</span>
              <span v-if="!(sourceDetail?.analysis.missingFields || []).length" class="line-chip line-chip--success">无缺口</span>
            </div>
          </section>

          <section class="sidebar-block">
            <h4>关注主题</h4>
            <ul class="line-list">
              <li v-for="item in sourceDetail?.analysis.focusTopics || []" :key="item">{{ item }}</li>
              <li v-if="!(sourceDetail?.analysis.focusTopics || []).length">暂无</li>
            </ul>
          </section>
        </article>

        <article class="workspace-panel sidebar-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">项目索引</p>
              <h3>原始画像</h3>
            </div>
            <span class="panel-meta">{{ sourceDetail?.projects.length || 0 }} 项</span>
          </div>

          <div v-if="sourceDetail?.projects.length" class="project-list">
            <article v-for="project in sourceDetail.projects" :key="project.projectId" class="project-card">
              <strong>{{ project.name }}</strong>
              <p>{{ project.summary || "暂无项目摘要" }}</p>
            </article>
          </div>
          <p v-else class="empty-copy">暂无项目经历。</p>
        </article>

        <article class="workspace-panel sidebar-panel">
          <div class="panel-head">
            <div>
              <p class="panel-kicker">草稿控制</p>
              <h3>本地暂存</h3>
            </div>
          </div>

          <button class="ghost-btn ghost-btn--dark" type="button" @click="resetDraft">撤销本地暂存</button>
        </article>
      </aside>
    </section>
  </section>

  <section v-else class="edit-loading">
    <div class="workspace-eyebrow">Profile Edit</div>
    <h2 class="workspace-title">{{ loadError || "正在加载候选人画像..." }}</h2>
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
.edit-shell {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid #ccd8e5;
  background: #f4f8fc;
}

.workspace-header {
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

.workspace-eyebrow,
.panel-kicker {
  margin: 0;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.workspace-title {
  margin: 10px 0 6px;
  font-size: 2rem;
  line-height: 1.1;
}

.workspace-meta {
  margin: 0;
  color: #56718b;
}

.workspace-meta--loading {
  color: #5c7289;
}

.workspace-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.ghost-btn,
.primary-btn {
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

.ghost-btn--dark {
  width: 100%;
  border-color: #c5d9ec;
  color: #1d64a1;
  background: #edf5fd;
}

.primary-btn {
  border: 1px solid #1f5f99;
  color: #ffffff;
  background: #1f5f99;
  cursor: pointer;
}

.save-alert {
  border-radius: 0;
}

.edit-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.8fr);
  gap: 14px;
}

.workspace-main,
.workspace-sidebar {
  display: grid;
  align-content: start;
  gap: 14px;
}

.workspace-panel {
  display: grid;
  gap: 16px;
  padding: 18px;
  border: 1px solid #d1dce7;
  background: #ffffff;
}

.sidebar-panel {
  gap: 14px;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.panel-head h2,
.panel-head h3,
.sidebar-block h4 {
  margin: 0;
}

.panel-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.panel-meta,
.field span,
.sidebar-copy,
.empty-copy {
  color: #5c7289;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding-top: 4px;
  border-top: 1px solid #e4ebf2;
}

.field-grid--wide {
  grid-template-columns: 1fr;
}

.field {
  display: grid;
  gap: 8px;
}

.field--full {
  grid-column: 1 / -1;
}

.field-input {
  width: 100%;
  min-height: 44px;
  padding: 10px 14px;
  border: 1px solid #c9d9ea;
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
  min-height: 140px;
}

.field-textarea--tall {
  min-height: 200px;
}

.sidebar-block,
.project-list {
  display: grid;
  gap: 10px;
}

.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.line-chip {
  display: inline-flex;
  align-items: center;
  min-height: 28px;
  padding: 0 10px;
  border-radius: 999px;
  background: #edf4fb;
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

.project-card {
  display: grid;
  gap: 8px;
  padding: 14px;
  border: 1px solid #dbe6f1;
  background: #fbfdff;
}

.project-card p {
  margin: 0;
  color: #5c7289;
  line-height: 1.6;
}

.edit-loading {
  display: grid;
  gap: 8px;
  padding: 24px;
  border: 1px solid #ccd8e5;
  border-left: 4px solid #1f5f99;
  background: #ffffff;
}

@media (max-width: 1080px) {
  .edit-workspace {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .edit-shell {
    padding: 16px;
  }

  .workspace-header,
  .panel-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .workspace-actions {
    justify-content: flex-start;
  }

  .field-grid {
    grid-template-columns: 1fr;
  }
}
</style>
