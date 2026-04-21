<template>
  <section v-if="task" class="task-detail-page">
    <article class="glass-card task-hero">
      <div class="page-head">
        <div>
          <div class="pill">Task Detail</div>
          <h2 class="section-title page-title">{{ task.title }}</h2>
          <p class="section-copy">{{ task.role }} · {{ task.status }}</p>
        </div>
        <div class="head-actions">
          <RouterLink class="secondary-btn" :to="{ name: 'admin-workbench' }">工作台</RouterLink>
          <RouterLink class="secondary-btn" :to="{ name: 'admin-candidates', query: { taskId: task.id } }">候选人</RouterLink>
        </div>
      </div>

      <div class="monitor-band" :class="{ 'monitor-band--active': hasActiveProcessing }">
        <div class="monitor-band-head">
          <div class="monitor-band-title">
            <span class="monitor-dot" :class="{ 'monitor-dot--pulse': hasActiveProcessing }"></span>
            <strong>{{ hasActiveProcessing ? "系统正在后台处理" : "系统最近一次状态" }}</strong>
          </div>
          <div class="monitor-meta">
            <span>{{ refreshing ? "正在拉取最新状态" : `上次同步 ${lastSyncedLabel}` }}</span>
            <span v-if="hasActiveProcessing">下次刷新 {{ nextRefreshSeconds }}s</span>
            <span>{{ hasActiveProcessing ? `处理中 ${activeUploadCount} 份` : "当前无进行中任务" }}</span>
          </div>
        </div>

        <div class="monitor-band-body">
          <div class="monitor-band-summary">
            <AdminToneBadge :label="monitorSummary.label" :tone="monitorSummary.tone" />
            <p class="monitor-band-copy">{{ monitorSummary.detail }}</p>
            <div class="monitor-band-footnote">刷新页面后会保留最近一次同步状态和动作记录。</div>
          </div>

          <div class="monitor-timeline" v-if="monitorEvents.length">
            <div class="monitor-timeline-label">系统刚刚做了什么</div>
            <div class="monitor-timeline-list">
              <article class="monitor-event" v-for="event in monitorEvents" :key="event.id">
                <div class="monitor-event-head">
                  <AdminToneBadge :label="event.label" :tone="event.tone" />
                  <span class="monitor-event-time">{{ formatTime(event.at) }}</span>
                </div>
                <div class="monitor-event-copy">{{ event.detail }}</div>
              </article>
            </div>
          </div>
        </div>
      </div>

      <div class="flow-panel">
        <div class="flow-summary">
          <div class="flow-copy">
            <AdminToneBadge :label="flowSummary.label" :tone="flowSummary.tone" />
            <p class="flow-text">{{ flowSummary.detail }}</p>
          </div>
          <AdminProgressMeter
            label="整体解析进度"
            :value="flowSummary.progress"
            :caption="flowProgressCaption"
            :tone="flowSummary.tone"
          />
        </div>

        <div class="flow-steps">
          <article
            v-for="(step, index) in taskFlowSteps"
            :key="step.label"
            class="flow-step"
            :class="{
              'flow-step--active': index === flowSummary.activeStep,
              'flow-step--done': index < flowSummary.activeStep || (index === flowSummary.activeStep && flowSummary.progress >= 100)
            }"
          >
            <div class="flow-step-index">{{ index + 1 }}</div>
            <div>
              <div class="flow-step-title">{{ step.label }}</div>
              <div class="flow-step-copy">{{ step.copy }}</div>
            </div>
          </article>
        </div>
      </div>

      <div class="metric-grid">
        <article class="metric-tile">
          <div class="metric-value">{{ task.uploads.length }}</div>
          <div class="metric-label">已上传简历</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ task.candidates.length }}</div>
          <div class="metric-label">解析候选人</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ parsingCount }}</div>
          <div class="metric-label">解析中</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ readyForPaperCount }}</div>
          <div class="metric-label">待发卷</div>
        </article>
      </div>
    </article>

    <article class="glass-card upload-card">
      <div class="panel-head">
        <div>
          <h3>上传 PDF 简历</h3>
          <p class="section-copy">支持一次上传多个 PDF。上传后会自动创建候选人占位，并展示每份简历当前所处阶段。</p>
        </div>
        <input
          ref="fileInputRef"
          class="file-input"
          type="file"
          accept="application/pdf"
          multiple
          @change="handleFileSelect"
        />
      </div>

      <div class="upload-actions">
        <button class="primary-btn" type="button" @click="openPicker">选择 PDF</button>
        <button class="secondary-btn" type="button" :disabled="refreshing" @click="refreshTask">
          {{ refreshing ? "刷新中..." : "刷新状态" }}
        </button>
      </div>

      <div v-if="uploadMessage" class="info-banner">{{ uploadMessage }}</div>

      <div class="system-strip">
        <div>
          <div class="system-strip-label">系统当前动作</div>
          <div class="system-strip-value">{{ monitorSummary.label }}</div>
        </div>
        <div class="system-strip-copy">{{ monitorSummary.detail }}</div>
      </div>

      <div v-if="uploadEntries.length" class="upload-list">
        <article class="upload-item" v-for="upload in uploadEntries" :key="upload.id">
          <div class="upload-head">
            <div>
              <strong>{{ upload.fileName }}</strong>
              <div class="upload-meta">最近更新 {{ formatTime(upload.updatedAt) }}</div>
            </div>
            <div class="upload-badges">
              <AdminToneBadge :label="upload.stage.label" :tone="upload.stage.tone" />
              <AdminToneBadge :label="`进度 ${upload.stage.progress}%`" :tone="upload.stage.tone" />
            </div>
          </div>

          <AdminProgressMeter
            label="当前阶段"
            :value="upload.stage.progress"
            :caption="upload.stage.detail"
            :tone="upload.stage.tone"
          />

          <div v-if="upload.steps.length" class="upload-step-row">
            <span
              v-for="step in upload.steps"
              :key="`${upload.id}-${step.label}`"
              class="upload-step-chip"
              :class="`upload-step-chip--${step.status}`"
            >
              {{ step.label }}
            </span>
          </div>

          <div class="upload-footer">
            <div class="upload-note">{{ upload.stage.detail }}</div>
            <RouterLink
              v-if="upload.candidateId"
              class="secondary-btn inline-btn"
              :to="{ name: 'admin-candidate-detail', params: { candidateId: upload.candidateId } }"
            >
              查看候选人
            </RouterLink>
          </div>
        </article>
      </div>

      <div v-else class="empty-state">还没有上传 PDF，任务会在收到第一份简历后开始生成候选人占位。</div>
    </article>

    <article class="glass-card candidate-card">
      <div class="panel-head">
        <div>
          <h3>任务候选人</h3>
          <p class="section-copy">这里保留每位候选人的最新解析摘要和下一步入口。</p>
        </div>
      </div>

      <div v-if="candidateEntries.length" class="candidate-list">
        <article class="candidate-item" v-for="candidate in candidateEntries" :key="candidate.id">
          <div class="candidate-main">
            <div class="candidate-head">
              <div>
                <strong>{{ candidate.name }}</strong>
                <div class="candidate-meta">{{ candidate.role }} · {{ candidate.city }}</div>
              </div>
              <div class="candidate-badges">
                <AdminToneBadge :label="candidate.status" :tone="candidate.statusTone" />
                <AdminToneBadge :label="`解析质量 ${candidate.quality}`" :tone="candidate.qualityTone" />
              </div>
            </div>
            <p class="candidate-summary">{{ candidate.summary }}</p>
            <div v-if="candidate.processingMessage" class="candidate-processing">{{ candidate.processingMessage }}</div>
            <div class="tag-row">
              <span class="tag-chip" v-for="skill in candidate.skills" :key="skill">{{ skill }}</span>
            </div>
          </div>

          <div class="candidate-actions">
            <RouterLink class="secondary-btn inline-btn" :to="buildCandidateDetailPath(candidate.id)">详情</RouterLink>
            <RouterLink class="primary-btn inline-btn" :to="paperTarget(candidate)">发卷</RouterLink>
          </div>
        </article>
      </div>

      <div v-else class="empty-state">解析完成后，候选人会出现在这里并给出发卷入口。</div>
    </article>
  </section>

  <section v-else class="glass-card task-empty">
    <div class="pill">Task Detail</div>
    <h2 class="section-title">{{ loadError || "正在加载任务详情..." }}</h2>
    <p v-if="monitorState" class="section-copy">
      已恢复上次同步状态：{{ monitorState.label }} · {{ formatTime(monitorState.lastSyncedAt) }}
    </p>
    <div v-if="monitorState?.events.length" class="task-empty-events">
      <article class="monitor-event" v-for="event in monitorState.events.slice(0, 3)" :key="event.id">
        <div class="monitor-event-head">
          <AdminToneBadge :label="event.label" :tone="event.tone" />
          <span class="monitor-event-time">{{ formatTime(event.at) }}</span>
        </div>
        <div class="monitor-event-copy">{{ event.detail }}</div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AdminProgressMeter from "../../components/admin/AdminProgressMeter.vue";
import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import { buildCandidateDetailPath, buildPaperEditorPath } from "../../components/admin/adminRouting";
import { describeUploadStage, summarizeTaskFlow, type AdminTone } from "../../components/admin/adminUi";
import { buildTaskMonitorState, readTaskMonitor, writeTaskMonitor, type TaskMonitorState } from "../../components/admin/taskMonitor";
import { loadTaskDetail, uploadTaskResumes, type CandidateCard } from "../../lib/gateway";

const POLLING_INTERVAL_MS = 1_200;

const route = useRoute();
const task = ref<Awaited<ReturnType<typeof loadTaskDetail>> | null>(null);
const loadError = ref("");
const uploadMessage = ref("");
const refreshing = ref(false);
const fileInputRef = ref<HTMLInputElement | null>(null);
const monitorState = ref<TaskMonitorState | null>(null);
const clockNow = ref(Date.now());
const taskId = computed(() => (typeof route.params.taskId === "string" ? route.params.taskId : ""));
let pollingTimer: number | null = null;
let clockTimer: number | null = null;

const taskFlowSteps = [
  { label: "接收文件", copy: "创建候选人占位与解析任务。" },
  { label: "解析内容", copy: "抽取 PDF 文本层并触发补读。" },
  { label: "整理画像", copy: "生成技能、联系方式与摘要。" },
  { label: "进入待发卷", copy: "候选人就绪，继续发卷。" }
];

const parsingCount = computed(() => task.value?.uploads.filter((item) => item.status !== "parsed" && item.status !== "failed").length ?? 0);
const readyForPaperCount = computed(() => task.value?.candidates.filter((candidate) => candidate.status === "待发卷").length ?? 0);
const flowSummary = computed(() => summarizeTaskFlow(task.value?.uploads ?? []));
const monitorSummary = computed(() => monitorState.value ?? {
  label: flowSummary.value.label,
  detail: flowSummary.value.detail,
  tone: flowSummary.value.tone,
  progress: flowSummary.value.progress
});
const hasActiveProcessing = computed(() => monitorState.value?.isProcessing ?? parsingCount.value > 0);
const activeUploadCount = computed(() => monitorState.value?.activeUploadCount ?? parsingCount.value);
const lastSyncedLabel = computed(() =>
  monitorState.value ? formatTime(monitorState.value.lastSyncedAt) : "暂未同步"
);
const nextRefreshSeconds = computed(() => {
  if (!monitorState.value?.nextPollAt || !hasActiveProcessing.value) {
    return 0;
  }
  const delta = Date.parse(monitorState.value.nextPollAt) - clockNow.value;
  return Math.max(0, Math.ceil(delta / 1_000));
});
const flowProgressCaption = computed(() => {
  if (refreshing.value) {
    return "正在刷新任务状态...";
  }
  if (hasActiveProcessing.value) {
    return `自动轮询中 · 下次刷新 ${nextRefreshSeconds.value}s`;
  }
  return `上次同步 ${lastSyncedLabel.value}`;
});
const monitorEvents = computed(() => monitorState.value?.events ?? []);
const uploadEntries = computed(() =>
  (task.value?.uploads ?? []).map((upload) => ({
    ...upload,
    stage: describeUploadStage(upload),
    steps: Object.values(upload.processing?.steps ?? {})
  }))
);
const candidateEntries = computed(() =>
  (task.value?.candidates ?? []).map((candidate) => ({
    ...candidate,
    qualityTone: toneForQuality(candidate.quality),
    statusTone: toneForStatus(candidate.status),
    processingMessage: candidate.processing?.message ?? ""
  }))
);

function toneForQuality(quality: string): AdminTone {
  if (quality === "高") {
    return "success";
  }
  if (quality === "中") {
    return "warning";
  }
  if (quality === "低") {
    return "danger";
  }
  return "info";
}

function toneForStatus(status: string): AdminTone {
  if (status === "待发卷" || status === "已交卷") {
    return "success";
  }
  if (status === "解析失败") {
    return "danger";
  }
  if (status === "解析中") {
    return "info";
  }
  return "warning";
}

function formatTime(value: string) {
  return new Date(value).toLocaleString("zh-CN", {
    hour12: false,
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function startClock() {
  if (clockTimer != null) {
    return;
  }
  clockTimer = window.setInterval(() => {
    clockNow.value = Date.now();
  }, 1_000);
}

function stopClock() {
  if (clockTimer != null) {
    window.clearInterval(clockTimer);
    clockTimer = null;
  }
}

function startPolling() {
  stopPolling();
  pollingTimer = window.setInterval(() => {
    void refreshTask();
  }, POLLING_INTERVAL_MS);
}

function stopPolling() {
  if (pollingTimer != null) {
    window.clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

function openPicker() {
  fileInputRef.value?.click();
}

function paperTarget(candidate: CandidateCard) {
  return {
    path: buildPaperEditorPath(candidate.paperId),
    query: {
      candidateId: candidate.id,
      candidateName: candidate.name
    }
  };
}

function syncMonitorState(nextTask: NonNullable<typeof task.value>) {
  monitorState.value = buildTaskMonitorState({
    taskId: nextTask.id,
    taskTitle: nextTask.title,
    uploads: nextTask.uploads,
    previous: monitorState.value,
    pollingIntervalMs: POLLING_INTERVAL_MS
  });
  writeTaskMonitor(monitorState.value);
}

async function refreshTask() {
  if (!taskId.value) {
    return;
  }

  refreshing.value = true;
  try {
    task.value = await loadTaskDetail(taskId.value);
    loadError.value = "";
    syncMonitorState(task.value);
    if (!monitorState.value?.isProcessing) {
      stopPolling();
    } else if (pollingTimer == null) {
      startPolling();
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "任务详情加载失败。";
  } finally {
    refreshing.value = false;
  }
}

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  if (!files.length || !taskId.value) {
    return;
  }

  uploadMessage.value = `已接收 ${files.length} 份 PDF，系统正在创建解析任务；即使刷新页面，最近动作也会保留。`;
  const createdUploads = await uploadTaskResumes(taskId.value, files);
  if (task.value) {
    const existingUploads = task.value.uploads.filter(
      (item) => createdUploads.some((createdUpload) => createdUpload.id === item.id) === false
    );
    const optimisticUploads = [...existingUploads, ...createdUploads];
    task.value = {
      ...task.value,
      uploads: optimisticUploads
    };
    syncMonitorState(task.value);
  }
  await refreshTask();
  startPolling();
  input.value = "";
}

watch(
  taskId,
  async (nextTaskId) => {
    if (!nextTaskId) {
      task.value = null;
      monitorState.value = null;
      return;
    }
    monitorState.value = readTaskMonitor(nextTaskId);
    if (monitorState.value?.isProcessing) {
      startPolling();
    }
    await refreshTask();
  },
  { immediate: true }
);

startClock();

onBeforeUnmount(() => {
  stopPolling();
  stopClock();
});
</script>

<style scoped>
.task-detail-page {
  display: grid;
  gap: 20px;
}

.task-hero,
.upload-card,
.candidate-card,
.task-empty {
  padding: 24px;
}

.page-head,
.panel-head,
.upload-head,
.upload-footer,
.candidate-head,
.candidate-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-title {
  margin: 16px 0 0;
}

.head-actions,
.upload-actions,
.upload-badges,
.candidate-badges,
.candidate-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.flow-panel {
  display: grid;
  gap: 18px;
  margin-top: 20px;
  padding: 18px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.9), rgba(228, 242, 248, 0.82));
  border: 1px solid rgba(14, 116, 144, 0.08);
}

.monitor-band {
  display: grid;
  gap: 16px;
  margin-top: 20px;
  padding: 18px 20px;
  border-radius: 24px;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.08), rgba(255, 255, 255, 0.9));
  border: 1px solid rgba(15, 118, 110, 0.12);
}

.monitor-band--active {
  box-shadow: 0 20px 40px rgba(15, 118, 110, 0.08);
}

.monitor-band-head,
.monitor-band-title,
.monitor-meta,
.monitor-event-head,
.upload-step-row,
.task-empty-events {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.monitor-band-head {
  justify-content: space-between;
  align-items: center;
}

.monitor-band-title {
  align-items: center;
  font-size: 1rem;
}

.monitor-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.4);
}

.monitor-dot--pulse {
  background: var(--accent);
  box-shadow: 0 0 0 0 rgba(15, 118, 110, 0.32);
  animation: pulse 1.6s ease-out infinite;
}

.monitor-meta {
  color: var(--ink-soft);
  font-size: 0.9rem;
}

.monitor-band-body {
  display: grid;
  grid-template-columns: minmax(0, 0.92fr) minmax(0, 1.08fr);
  gap: 18px;
}

.monitor-band-summary,
.monitor-timeline {
  display: grid;
  gap: 12px;
}

.monitor-band-copy,
.monitor-band-footnote,
.monitor-timeline-label,
.monitor-event-copy,
.candidate-processing {
  color: var(--ink-soft);
}

.monitor-band-copy,
.monitor-event-copy,
.candidate-processing {
  line-height: 1.6;
}

.monitor-band-footnote,
.monitor-timeline-label,
.monitor-event-time {
  font-size: 0.86rem;
}

.monitor-timeline-list {
  display: grid;
  gap: 10px;
}

.monitor-event {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(20, 33, 61, 0.06);
}

.flow-summary {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(280px, 0.9fr);
  gap: 18px;
}

.flow-copy {
  display: grid;
  gap: 12px;
}

.flow-text {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

.flow-steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.flow-step {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 12px;
  padding: 16px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(20, 33, 61, 0.06);
}

.flow-step--active {
  border-color: rgba(14, 116, 144, 0.18);
  box-shadow: 0 14px 32px rgba(14, 116, 144, 0.08);
}

.flow-step--done {
  background: rgba(232, 245, 235, 0.82);
}

.flow-step-index {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.08);
  font-weight: 700;
}

.flow-step-title {
  font-weight: 700;
}

.flow-step-copy,
.upload-meta,
.candidate-meta,
.candidate-summary,
.empty-state {
  color: var(--ink-soft);
}

.flow-step-copy,
.candidate-summary,
.empty-state {
  line-height: 1.6;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.file-input {
  display: none;
}

.info-banner,
.system-strip {
  padding: 14px 16px;
  border-radius: 18px;
}

.info-banner {
  background: rgba(15, 118, 110, 0.1);
  color: var(--accent-strong);
}

.system-strip {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 14px;
  background: rgba(20, 33, 61, 0.04);
}

.system-strip-label {
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.system-strip-value {
  margin-top: 6px;
  font-size: 1.04rem;
  font-weight: 700;
}

.system-strip-copy {
  color: var(--ink-soft);
  line-height: 1.6;
}

.upload-list,
.candidate-list {
  display: grid;
  gap: 14px;
  margin-top: 18px;
}

.upload-item,
.candidate-item {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.upload-item {
  display: grid;
  gap: 14px;
}

.upload-note {
  color: var(--ink-soft);
  line-height: 1.6;
}

.upload-step-chip {
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
  font-size: 0.82rem;
}

.upload-step-chip--running {
  background: rgba(14, 165, 233, 0.12);
  color: #0369a1;
}

.upload-step-chip--succeeded {
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent-strong);
}

.upload-step-chip--failed {
  background: rgba(220, 38, 38, 0.12);
  color: var(--danger);
}

.candidate-processing {
  font-size: 0.92rem;
}

.candidate-item {
  align-items: stretch;
}

.candidate-main {
  display: grid;
  gap: 12px;
}

.candidate-head {
  align-items: flex-start;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.empty-state {
  padding: 20px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.04);
}

@media (max-width: 960px) {
  .page-head,
  .panel-head,
  .upload-head,
  .upload-footer,
  .candidate-head,
  .candidate-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .flow-summary,
  .monitor-band-body,
  .system-strip,
  .metric-grid,
  .flow-steps {
    grid-template-columns: 1fr;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(15, 118, 110, 0.28);
  }

  70% {
    box-shadow: 0 0 0 12px rgba(15, 118, 110, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(15, 118, 110, 0);
  }
}
</style>
