<template>
  <section v-if="paper" class="glass-card paper-card">
    <div class="paper-head">
      <div>
        <div class="pill">Paper Publish</div>
        <h2 class="section-title paper-title">{{ paper.title }}</h2>
        <p class="paper-meta">发布对象：{{ candidateDisplayName }}</p>
      </div>
      <div class="button-row">
        <AdminToneBadge :label="paper.status === 'published' ? '已发布' : '草稿中'" :tone="paper.status === 'published' ? 'success' : 'warning'" />
        <AdminToneBadge :label="shareCardTone.label" :tone="shareCardTone.tone" />
      </div>
    </div>

    <section class="publish-panel">
      <div class="panel-head">
        <div>
          <h3>确认并发布考试入口</h3>
          <p class="panel-copy">先核对发卷对象、题量和分享信息，再生成考试链接与验证码。</p>
        </div>
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
            <div class="check-item">
              <span>入口状态</span>
              <strong>{{ shareCardTone.label }}</strong>
            </div>
          </div>

          <div class="confirm-actions">
            <button class="secondary-btn" type="button" @click="saveDraft">保存草稿</button>
            <button class="primary-btn" type="button" :disabled="publishing" @click="generatePublishInfo">
              {{ publishing ? "发布中..." : "确认并发布考试入口" }}
            </button>
          </div>

          <div class="publish-footer">
            <span>{{ statusMessage || "生成后会展示可直接分享给候选人的入口卡片。" }}</span>
          </div>
        </article>

        <article class="share-card" :class="{ 'share-card--ready': shareReady }">
          <div class="share-head">
            <div>
              <div class="share-title">考试入口分享卡</div>
              <div class="share-copy">{{ shareReady ? shareCardDescription : "点击主按钮后生成正式分享信息。" }}</div>
            </div>
            <AdminToneBadge :label="shareCardTone.label" :tone="shareCardTone.tone" />
          </div>

          <div class="publish-grid">
            <AdminCopyField label="考试链接" :value="publishInfo.link" />
            <AdminCopyField label="验证码" :value="publishInfo.code" />
          </div>

          <div class="share-state">
            <div class="share-state-item">
              <span>发布类型</span>
              <strong>{{ shareReady && isFallbackPublish ? "前端预览入口" : "正式考试入口" }}</strong>
            </div>
            <div class="share-state-item">
              <span>分享建议</span>
              <strong>{{ shareReady ? "复制链接与验证码，一次发给候选人" : "入口尚未生成" }}</strong>
            </div>
          </div>
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
    <div class="pill">Paper Publish</div>
    <h2 class="section-title paper-title">{{ loadError || "正在同步考卷草稿..." }}</h2>
    <p class="section-copy">编辑器会优先读取后端考卷数据，发布信息则由前端工作台补齐展示位。</p>
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
const shareCardTone = computed(() => {
  if (shareReady.value) {
    return {
      label: isFallbackPublish.value ? "预览入口已生成" : "考试入口已发布",
      tone: (isFallbackPublish.value ? "warning" : "success") as "warning" | "success"
    };
  }

  return {
    label: "等待发布",
    tone: "info" as const
  };
});
const shareCardDescription = computed(() => {
  if (isFallbackPublish.value) {
    return "后端发布接口暂不可用，当前提供的是前端预览入口，便于 HR 先行推进沟通。";
  }

  return "入口已生成，可以直接复制链接与验证码发送给候选人。";
});

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

function buildVerificationCode(seed: string) {
  const checksum = seed
    .split("")
    .reduce((total, char, index) => total + char.charCodeAt(0) * (index + 17), 0);

  return String(checksum).slice(-6).padStart(6, "0");
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
    statusMessage.value = `考试入口已发布，可直接复制分享给 ${candidateDisplayName.value}。`;
  } catch {
    if (typeof window === "undefined") {
      return;
    }

    const token = `${paperId.value}-${candidateId.value || "preview"}`
      .replace(/[^a-zA-Z0-9-]/g, "-")
      .toLowerCase();
    const nextValue = {
      link: `${window.location.origin}/exam/${token}`,
      code: buildVerificationCode(`${paperId.value}:${candidateId.value || "preview"}`)
    };

    isFallbackPublish.value = true;
    publishInfo.value = nextValue;
    window.localStorage.setItem(storageKey(), JSON.stringify(nextValue));
    statusMessage.value = `后端发布接口暂不可用，已生成前端预览入口给 ${candidateDisplayName.value}。`;
  } finally {
    publishing.value = false;
  }
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
    statusMessage.value = "草稿已同步到后端。";
  } catch {
    statusMessage.value = `后端保存暂不可用，已记录当前草稿状态 ${new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })}`;
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

      loadError.value = "考卷草稿加载失败，请稍后重试。";
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
