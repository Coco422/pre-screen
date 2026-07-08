<template>
  <section v-if="paper" class="glass-card paper-card">
    <div class="paper-head">
      <div>
        <div class="pill">考卷</div>
        <h2 class="section-title paper-title">{{ paper.title }}</h2>
        <p class="paper-meta">{{ candidateDisplayName }}</p>
      </div>
      <div class="button-row">
        <AdminToneBadge :label="paper.status === 'published' ? '已发布' : '草稿'" :tone="paper.status === 'published' ? 'success' : 'warning'" />
      </div>
    </div>

    <section class="publish-panel">
      <div class="panel-head">
        <h3>发布考试入口</h3>
        <RouterLink class="secondary-btn" :to="{ name: 'admin-candidates' }">返回候选人</RouterLink>
      </div>

      <div class="publish-layout">
        <article class="confirm-card">
          <div class="confirm-title">发布前检查</div>
          <div class="checklist">
            <div class="check-item">
              <span>发卷对象</span>
              <strong>{{ candidateDisplayName }}</strong>
            </div>
            <div class="check-item">
              <span>考试时长</span>
              <strong>{{ paper.durationMinutes }} 分钟</strong>
            </div>
            <div class="check-item">
              <span>题目总数</span>
              <strong>{{ paper.questions.length }} 题</strong>
            </div>
          </div>

          <div class="confirm-actions">
            <button class="secondary-btn" type="button" @click="saveDraft">保存草稿</button>
            <button class="primary-btn" type="button" :disabled="publishing" @click="generatePublishInfo">
              {{ publishing ? "发布中..." : "确认发布" }}
            </button>
          </div>

          <div v-if="statusMessage" class="publish-footer">
            <span>{{ statusMessage }}</span>
          </div>
        </article>

        <article class="share-card" :class="{ 'share-card--ready': shareReady }">
          <div class="share-head">
            <div class="share-title">分享卡</div>
            <AdminToneBadge v-if="shareReady" label="已生成" tone="success" />
            <AdminToneBadge v-else label="待发布" tone="info" />
          </div>

          <div class="publish-grid">
            <AdminCopyField label="考试链接" :value="publishInfo.link" />
            <AdminCopyField label="验证码" :value="publishInfo.code" />
          </div>

          <button
            v-if="shareReady"
            class="primary-btn copy-all-btn"
            type="button"
            @click="copyAll"
          >一键复制</button>
        </article>
      </div>
    </section>

    <div class="paper-layout">
      <aside class="outline-panel">
        <div class="outline-title">题目结构</div>
        <div class="outline-item" v-for="item in outline" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.count }}</strong>
        </div>
      </aside>

      <div class="question-stack">
        <article class="question-card" v-for="question in paper.questions" :key="question.id">
          <div class="question-top">
            <div>
              <div class="question-type">{{ questionKindLabel(question.kind) }}</div>
              <h3>{{ question.title }}</h3>
            </div>
            <span class="pill">{{ question.score }} 分</span>
          </div>
          <p class="section-copy">{{ question.description }}</p>
        </article>
      </div>
    </div>
  </section>

  <section v-else class="glass-card paper-card">
    <div class="pill">考卷</div>
    <h2 class="section-title paper-title">{{ loadError || "加载中" }}</h2>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";

import AdminCopyField from "../../components/admin/AdminCopyField.vue";
import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import { generatePaper, loadPaperDraft, publishPaper, savePaperDraft, type PaperDraft } from "../../lib/gateway";

type PublishInfo = {
  link: string;
  code: string;
};

const route = useRoute();
const router = useRouter();
const paper = ref<PaperDraft | null>(null);
const publishInfo = ref<PublishInfo>({ link: "", code: "" });
const loadError = ref("");
const statusMessage = ref("");
const publishing = ref(false);
const isFallbackPublish = ref(false);
let latestRequestId = 0;

const paperId = computed(() => (typeof route.params.paperId === "string" ? route.params.paperId : "new"));
const candidateId = computed(() => (typeof route.query.candidateId === "string" ? route.query.candidateId : ""));
const candidateDisplayName = computed(() => {
  if (typeof route.query.candidateName === "string" && route.query.candidateName.length) {
    return route.query.candidateName;
  }

  return candidateId.value ? `候选人 ${candidateId.value}` : "预览模式";
});

const outline = computed(() => {
  if (!paper.value) {
    return [];
  }

  return [
    { label: "基础信息", count: paper.value.mix.base_info ?? 0 },
    { label: "客观题", count: paper.value.mix.objective ?? 0 },
    { label: "主观题", count: paper.value.mix.subjective ?? 0 },
    { label: "代码题", count: paper.value.mix.coding ?? 0 }
  ];
});
const shareReady = computed(() => Boolean(publishInfo.value.link && publishInfo.value.code));

function storageKey() {
  return `admin-paper-publish:${paperId.value}:${candidateId.value || "preview"}`;
}

function readPublishInfo(): PublishInfo {
  if (typeof window === "undefined") {
    return { link: "", code: "" };
  }

  const raw = window.localStorage.getItem(storageKey());
  if (!raw) {
    return { link: "", code: "" };
  }

  try {
    return JSON.parse(raw) as PublishInfo;
  } catch {
    return { link: "", code: "" };
  }
}

function questionKindLabel(kind: string) {
  switch (kind) {
    case "base_info":
      return "基础信息";
    case "objective":
      return "客观题";
    case "subjective":
      return "主观题";
    case "coding":
      return "代码题";
    default:
      return kind;
  }
}

async function generatePublishInfo() {
  if (!paper.value) {
    return;
  }

  publishing.value = true;
  try {
    const invitation = await publishPaper(paperId.value);
    const nextValue = {
      link: invitation?.startUrl ?? "",
      code: invitation?.verifyCode ?? ""
    };

    isFallbackPublish.value = false;
    publishInfo.value = nextValue;
    paper.value = {
      ...paper.value,
      status: "published",
      invitation
    };
    if (typeof window !== "undefined") {
      window.localStorage.setItem(storageKey(), JSON.stringify(nextValue));
    }
    statusMessage.value = "已发布";
  } catch (error) {
    statusMessage.value = error instanceof Error ? error.message : "发布失败";
  } finally {
    publishing.value = false;
  }
}

async function copyAll() {
  const text = `考试链接：${publishInfo.value.link}\n验证码：${publishInfo.value.code}`;
  await navigator.clipboard.writeText(text);
  statusMessage.value = "已复制到剪贴板";
}

async function saveDraft() {
  if (!paper.value) {
    return;
  }

  try {
    paper.value = await savePaperDraft(paperId.value, {
      title: paper.value.title,
      durationMinutes: paper.value.durationMinutes,
      introduction: paper.value.introduction,
      questions: paper.value.questions
    });
    statusMessage.value = "已保存";
  } catch (error) {
    statusMessage.value = error instanceof Error ? error.message : "保存失败";
  }
}

watch(
  [paperId, candidateId],
  async ([nextPaperId, nextCandidateId]) => {
    const requestId = ++latestRequestId;
    paper.value = null;
    loadError.value = "";
    statusMessage.value = "";
    publishInfo.value = readPublishInfo();
    isFallbackPublish.value = Boolean(publishInfo.value.link && publishInfo.value.code);

    try {
      const draft =
        nextPaperId === "new" && nextCandidateId
          ? await generatePaper(nextCandidateId)
          : await loadPaperDraft(nextPaperId);
      if (requestId !== latestRequestId) {
        return;
      }

      paper.value = draft;
      if (nextPaperId === "new") {
        await router.replace({
          name: "admin-paper-editor",
          params: { paperId: draft.paperId },
          query: route.query
        });
      }
      if (draft.invitation) {
        publishInfo.value = {
          link: draft.invitation.startUrl,
          code: draft.invitation.verifyCode
        };
        isFallbackPublish.value = false;
      }
    } catch {
      if (requestId !== latestRequestId) {
        return;
      }

      loadError.value = "加载失败";
    }
  },
  { immediate: true }
);
</script>

<style scoped>
.paper-card {
  display: grid;
  gap: 24px;
  padding: 24px;
}

.paper-head,
.panel-head,
.question-top,
.publish-footer,
.share-head,
.check-item,
.share-state-item {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.button-row,
.confirm-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.paper-title {
  margin-top: 16px;
  font-size: 2rem;
}

.paper-meta,
.panel-copy,
.publish-footer,
.share-copy,
.check-item span,
.share-state-item span {
  color: var(--ink-soft);
}

.paper-meta,
.panel-copy {
  margin: 12px 0 0;
}

.publish-panel {
  display: grid;
  gap: 18px;
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.panel-head h3,
.outline-title,
.confirm-title,
.share-title {
  margin: 0;
  font-weight: 700;
}

.publish-layout {
  display: grid;
  grid-template-columns: minmax(280px, 0.9fr) minmax(0, 1.1fr);
  gap: 18px;
}

.confirm-card,
.share-card {
  display: grid;
  gap: 16px;
  padding: 20px;
  border-radius: 22px;
  background: rgba(20, 33, 61, 0.04);
}

.share-card {
  border: 1px solid rgba(20, 33, 61, 0.06);
}

.share-card--ready {
  background: linear-gradient(135deg, rgba(244, 252, 247, 0.92), rgba(235, 247, 255, 0.9));
  border-color: rgba(22, 163, 74, 0.12);
}

.checklist,
.share-state {
  display: grid;
  gap: 12px;
}

.check-item,
.share-state-item {
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(20, 33, 61, 0.06);
}

.publish-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.copy-all-btn {
  margin-top: 14px;
  width: 100%;
}

.paper-layout {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 24px;
}

.outline-panel {
  padding: 18px;
  border-radius: 22px;
  background: rgba(20, 33, 61, 0.04);
}

.outline-item {
  display: flex;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid rgba(20, 33, 61, 0.06);
}

.question-stack {
  display: grid;
  gap: 16px;
}

.question-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.question-type {
  color: var(--accent-strong);
  font-size: 0.88rem;
  font-weight: 700;
}

.question-card h3 {
  margin: 8px 0 0;
}

@media (max-width: 960px) {
  .paper-head,
  .panel-head,
  .question-top,
  .publish-footer,
  .share-head,
  .check-item,
  .share-state-item {
    flex-direction: column;
  }

  .publish-layout,
  .publish-grid,
  .paper-layout {
    grid-template-columns: 1fr;
  }
}
</style>
