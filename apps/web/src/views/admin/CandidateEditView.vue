<template>
  <section v-if="ready" class="glass-card edit-card">
    <div class="page-head">
      <div>
        <div class="pill">Profile Edit</div>
        <h2 class="section-title page-title">编辑候选人画像</h2>
      </div>
      <div class="button-row">
        <RouterLink class="secondary-btn" :to="detailTarget">返回详情</RouterLink>
        <RouterLink class="secondary-btn" :to="paperTarget">去发卷</RouterLink>
        <button class="primary-btn" type="button" @click="saveDraft">保存画像</button>
      </div>
    </div>

    <div v-if="saveMessage" class="save-banner">{{ saveMessage }}</div>

    <div class="form-grid">
      <label class="field">
        <span>姓名</span>
        <input v-model="form.name" class="soft-input" />
      </label>
      <label class="field">
        <span>岗位</span>
        <input v-model="form.role" class="soft-input" />
      </label>
      <label class="field">
        <span>邮箱</span>
        <input v-model="form.email" class="soft-input" />
      </label>
      <label class="field">
        <span>城市</span>
        <input v-model="form.city" class="soft-input" />
      </label>
      <label class="field">
        <span>电话</span>
        <input v-model="form.phone" class="soft-input" />
      </label>
      <label class="field field--full">
        <span>技能标签（逗号分隔）</span>
        <input v-model="form.skillsText" class="soft-input" />
      </label>
      <label class="field field--full">
        <span>爱好标签（逗号分隔）</span>
        <input v-model="form.hobbiesText" class="soft-input" />
      </label>
      <label class="field">
        <span>身高（cm）</span>
        <input v-model="form.heightCmText" class="soft-input" />
      </label>
      <label class="field">
        <span>体重（kg）</span>
        <input v-model="form.weightKgText" class="soft-input" />
      </label>
      <label class="field">
        <span>可到岗天数</span>
        <input v-model="form.availableInDaysText" class="soft-input" />
      </label>
      <label class="field field--full">
        <span>项目摘要</span>
        <textarea v-model="form.projectSummary" class="soft-input soft-textarea" rows="5" />
      </label>
      <label class="field field--full">
        <span>复核备注（每行一条）</span>
        <textarea v-model="form.reviewNotesText" class="soft-input soft-textarea" rows="5" />
      </label>
    </div>

    <div class="footer-actions">
      <button class="secondary-btn" type="button" @click="resetDraft">撤销本地暂存</button>
      <span class="footer-copy">当前编辑结果先存本地草稿，待后端保存接口就绪后可直接接入。</span>
    </div>
  </section>

  <section v-else class="glass-card edit-card">
    <div class="pill">Profile Edit</div>
    <h2 class="section-title page-title">{{ loadError || "正在加载候选人画像..." }}</h2>
    <p class="section-copy">编辑页会先读取候选人详情，再叠加本地暂存草稿。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import {
  buildCandidateDetailPath,
  buildPaperEditorPath,
  buildPaperRouteTarget
} from "../../components/admin/adminRouting";
import { loadCandidateDetail, type CandidateDetail, updateCandidateDetail } from "../../lib/gateway";

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

function applyToForm(detail: CandidateDetail, draft: Partial<CandidateDraft> | null) {
  const merged = {
    ...detail,
    ...draft,
    skills: Array.isArray(draft?.skills) && draft.skills.length ? draft.skills : detail.skills,
    reviewNotes: Array.isArray(draft?.reviewNotes) && draft.reviewNotes.length ? draft.reviewNotes : detail.reviewNotes
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

  const payload = buildDraftPayload();

  try {
    const detail = await updateCandidateDetail(candidateId.value, payload);
    sourceDetail.value = detail;
    clearDraft(candidateId.value);
    applyToForm(detail, null);
    saveMessage.value = "画像已同步到后端。";
  } catch {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(`admin-candidate-draft:${candidateId.value}`, JSON.stringify(payload));
    }
    saveMessage.value = `后端保存暂不可用，已保存本地草稿 ${new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
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
.edit-card {
  display: grid;
  gap: 20px;
  padding: 24px;
}

.page-head,
.button-row,
.footer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.button-row {
  flex-wrap: wrap;
}

.page-title {
  margin: 16px 0 0;
}

.save-banner {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(15, 118, 110, 0.1);
  color: var(--accent-strong);
  font-weight: 600;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
}

.field span,
.footer-copy {
  color: var(--ink-soft);
}

.field--full {
  grid-column: 1 / -1;
}

.soft-textarea {
  resize: vertical;
  min-height: 132px;
}

.footer-actions {
  flex-wrap: wrap;
}

@media (max-width: 960px) {
  .page-head,
  .button-row,
  .footer-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
