<template>
  <section v-if="task" class="task-detail-page">
    <article class="task-detail-section task-hero">
      <div class="page-head">
        <div>
          <h2 class="page-title">{{ task.title }} · {{ task.status }}</h2>
          <!-- <p class="page-subtitle">{{ task.role }} · {{ task.status }}</p> -->
        </div>
        <div class="head-actions">
          <RouterLink class="outline-btn" :to="{ name: 'admin-tasks' }">返回任务中心</RouterLink>
          <RouterLink class="outline-btn" :to="{ name: 'admin-candidates', query: { taskId: task.id } }">查看候选人</RouterLink>
        </div>
      </div>

      <div class="flow-panel">
        <div class="flow-panel-head">
          <div class="flow-panel-title">
            <span class="monitor-dot" :class="{ 'monitor-dot--pulse': hasActiveProcessing }"></span>
            <strong>处理进度</strong>
          </div>
          <div class="monitor-meta">
            <span>{{ refreshing ? "正在拉取最新状态" : `上次同步 ${lastSyncedLabel}` }}</span>
            <span v-if="hasActiveProcessing">下次刷新 {{ nextRefreshSeconds }}s</span>
            <span>{{ hasActiveProcessing ? `处理中 ${activeUploadCount} 份` : "当前无进行中任务" }}</span>
          </div>
        </div>

        <div class="flow-summary">
          <div class="flow-copy">
            <div class="flow-card-title">当前状态</div>
            <div class="flow-status-row">
              <AdminToneBadge :label="monitorSummary.label" :tone="monitorSummary.tone" />
              <strong>{{ monitorSummary.progress }}%</strong>
            </div>
            <el-progress
              :percentage="monitorSummary.progress"
              :show-text="false"
              :stroke-width="8"
              :status="progressStatus(monitorSummary.tone)"
            />
            <p class="flow-text">{{ monitorSummary.detail }}</p>
          </div>
          <div class="flow-progress-card">
            <div class="flow-card-title">整体解析进度</div>
            <div class="flow-status-row">
              <span>{{ flowProgressCaption }}</span>
              <strong>{{ flowSummary.progress }}%</strong>
            </div>
            <el-progress
              :percentage="flowSummary.progress"
              :show-text="false"
              :stroke-width="8"
              :status="progressStatus(flowSummary.tone)"
            />
          </div>
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

        <div class="monitor-timeline" v-if="monitorEvents.length">
          <div class="monitor-timeline-label">最近动作</div>
          <div class="monitor-timeline-list">
            <article class="monitor-event" v-for="event in monitorEvents.slice(0, 3)" :key="event.id">
              <div class="monitor-event-head">
                <AdminToneBadge :label="event.label" :tone="event.tone" />
                <span class="monitor-event-time">{{ formatTime(event.at) }}</span>
              </div>
              <div class="monitor-event-copy">{{ event.detail }}</div>
            </article>
          </div>
        </div>
      </div>
    </article>

    <div class="task-detail-grid">
    <article class="task-detail-section upload-card">
      <div class="upload-actions">
        <el-upload
          class="resume-upload"
          drag
          multiple
          accept="application/pdf"
          action="#"
          :show-file-list="false"
          :http-request="uploadResumeRequest"
          :before-upload="beforeResumeUpload"
        >
          <el-icon class="resume-upload__icon"><UploadFilled /></el-icon>
          <div class="resume-upload__text">点击或拖拽 PDF 到这里上传</div>
          <template #tip>
            <div class="resume-upload__tip">支持多个 PDF</div>
          </template>
        </el-upload>
        <button class="outline-btn" type="button" :disabled="refreshing" @click="refreshTask">
          {{ refreshing ? "刷新中..." : "刷新状态" }}
        </button>
      </div>

      <div v-if="uploadMessage" class="info-banner">{{ uploadMessage }}</div>

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
              class="outline-btn inline-btn"
              :to="{ name: 'admin-candidate-detail', params: { candidateId: upload.candidateId } }"
            >
              查看候选人
            </RouterLink>
          </div>
        </article>
      </div>

      <div v-else class="empty-state">还没有上传 PDF，任务会在收到第一份简历后开始生成候选人占位。</div>
    </article>

    <article class="task-detail-section candidate-card">
      <div class="panel-head">
        <div>
          <h3>任务候选人</h3>
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
            <RouterLink class="outline-btn inline-btn" :to="buildCandidateDetailPath(candidate.id)">
              详情 / 简历预览
            </RouterLink>
            <button
              v-if="isPaperGenerating(candidate)"
              class="outline-btn inline-btn"
              type="button"
              disabled
            >
              生成中 {{ candidate.processing?.progress ?? 0 }}%
            </button>
            <button
              v-else-if="canStartPaperGeneration(candidate)"
              class="primary-action inline-btn"
              type="button"
              :disabled="generatingIds.has(candidate.id)"
              @click="startGeneratePaper(candidate)"
            >
              {{ generatingIds.has(candidate.id) ? "提交中..." : "生成考卷" }}
            </button>
            <RouterLink
              v-else-if="candidate.paperId"
              class="primary-action inline-btn"
              :to="paperEditorTarget(candidate)"
            >
              编辑考卷
            </RouterLink>
          </div>
        </article>
      </div>

      <div v-else class="empty-state">解析完成后，候选人会出现在这里并给出发卷入口。</div>
    </article>
    </div>
  </section>

  <section v-else class="task-detail-section task-empty">
    <h2>{{ loadError || "正在加载任务详情..." }}</h2>
    <p v-if="monitorState">
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
import type { UploadRequestOptions } from "element-plus";

import { UploadFilled } from "@element-plus/icons-vue";
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import AdminProgressMeter from "../../components/admin/AdminProgressMeter.vue";
import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import { buildCandidateDetailPath, buildPaperEditorPath } from "../../components/admin/adminRouting";
import { describeUploadStage, summarizeTaskFlow, type AdminTone } from "../../components/admin/adminUi";
import { buildTaskMonitorState, readTaskMonitor, writeTaskMonitor, type TaskMonitorState } from "../../components/admin/taskMonitor";
import {
  loadTaskDetail,
  startPaperGeneration,
  uploadTaskResumes,
  type CandidateCard
} from "../../lib/gateway";

const POLLING_INTERVAL_MS = 1_200;

const route = useRoute();
const task = ref<Awaited<ReturnType<typeof loadTaskDetail>> | null>(null);
const loadError = ref("");
const uploadMessage = ref("");
const refreshing = ref(false);
const generatingIds = ref(new Set<string>());
const monitorState = ref<TaskMonitorState | null>(null);
const clockNow = ref(Date.now());
const taskId = computed(() => (typeof route.params.taskId === "string" ? route.params.taskId : ""));
let pollingTimer: number | null = null;
let clockTimer: number | null = null;

const taskFlowSteps = [
  { label: "接收文件", copy: "创建候选人占位与解析任务。" },
  { label: "解析内容", copy: "抽取 PDF 文本层并触发补读。" },
  { label: "整理画像", copy: "生成技能、联系方式与摘要。" },
  { label: "生成考卷", copy: "异步出题，完成后可编辑并发布。" }
];

const paperGeneratingCount = computed(
  () =>
    task.value?.candidates.filter((item) => isPaperGenerating(item)).length ?? 0
);
const parsingCount = computed(() => {
  const uploadBusy =
    task.value?.uploads.filter((item) => item.status !== "parsed" && item.status !== "failed").length ?? 0;
  return uploadBusy + paperGeneratingCount.value;
});
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
  if (status === "待发卷" || status === "已交卷" || status === "已完成筛选") {
    return "success";
  }
  if (status === "解析失败" || status === "已淘汰") {
    return "danger";
  }
  if (status === "解析中" || status === "拟出卷中") {
    return "info";
  }
  return "warning";
}

function isPaperGenerating(candidate: CandidateCard) {
  if (candidate.status === "拟出卷中") {
    return true;
  }
  const stage = candidate.processing?.stage;
  const status = candidate.processing?.status;
  return stage === "paper_generate" && (status === "running" || status === "queued");
}

function canStartPaperGeneration(candidate: CandidateCard) {
  if (candidate.paperId || isPaperGenerating(candidate)) {
    return false;
  }
  if (candidate.status === "解析中" || candidate.status === "解析失败") {
    return false;
  }
  return true;
}

function paperEditorTarget(candidate: CandidateCard) {
  return {
    path: buildPaperEditorPath(candidate.paperId),
    query: {
      candidateId: candidate.id,
      candidateName: candidate.name
    }
  };
}

async function startGeneratePaper(candidate: CandidateCard) {
  const next = new Set(generatingIds.value);
  next.add(candidate.id);
  generatingIds.value = next;
  uploadMessage.value = `已为 ${candidate.name} 提交考卷生成任务，可继续处理其他候选人。`;
  try {
    await startPaperGeneration(candidate.id);
    await refreshTask();
    if (pollingTimer == null) {
      startPolling();
    }
  } catch (error) {
    uploadMessage.value = error instanceof Error ? error.message : "提交考卷生成失败";
  } finally {
    const cleared = new Set(generatingIds.value);
    cleared.delete(candidate.id);
    generatingIds.value = cleared;
  }
}

function progressStatus(tone: AdminTone) {
  if (tone === "success" || tone === "warning" || tone === "danger") {
    return tone;
  }
  return undefined;
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
    loadError.value = error instanceof Error ? error.message : "加载失败";
  } finally {
    refreshing.value = false;
  }
}

function beforeResumeUpload(file: File) {
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    uploadMessage.value = "仅支持上传 PDF 文件。";
    return false;
  }
  return true;
}

function buildUploadError(message: string) {
  return Object.assign(new Error(message), {
    name: "UploadAjaxError",
    status: 0,
    method: "POST",
    url: `/admin/tasks/${taskId.value}/uploads`
  });
}

async function uploadResumeRequest(options: UploadRequestOptions) {
  if (!taskId.value) {
    options.onError(buildUploadError("任务不存在，无法上传。"));
    return;
  }

  const file = options.file;
  uploadMessage.value = `已接收 ${file.name}，系统正在创建解析任务。`;
  try {
    const createdUploads = await uploadTaskResumes(taskId.value, [file]);
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
    options.onSuccess(createdUploads);
  } catch (error) {
    const message = error instanceof Error ? error.message : "上传失败。";
    uploadMessage.value = message;
    options.onError(buildUploadError(message));
  }
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
  gap: 14px;
  min-width: 0;
}

.task-detail-section {
  min-width: 0;
  padding: 16px;
  border-radius: 8px;
  background: #ffffff;
}

.task-detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
  gap: 14px;
  min-width: 0;
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
  min-width: 0;
}

.page-title,
.task-empty h2,
.panel-head h3 {
  margin: 0;
  color: #17253d;
  font-weight: 800;
  letter-spacing: 0;
}

.page-title {
  font-size: 20px;
}

.page-subtitle,
.panel-head p,
.task-empty p,
.flow-text,
.monitor-timeline-label,
.monitor-event-copy,
.upload-meta,
.upload-note,
.candidate-meta,
.candidate-summary,
.candidate-processing,
.empty-state {
  color: #66758a;
}

.page-subtitle,
.panel-head p {
  margin: 6px 0 0;
  font-size: 13px;
}

.head-actions,
.upload-actions,
.upload-badges,
.candidate-badges,
.candidate-actions,
.upload-step-row,
.task-empty-events {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.outline-btn,
.primary-action {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
  padding: 0 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
}

.outline-btn {
  border: 1px solid #d7e2ef;
  background: #ffffff;
  color: #40546f;
}

.primary-action {
  border: 1px solid #2f69d9;
  background: #2f6cf6;
  color: #ffffff;
}

.outline-btn:disabled,
.primary-action:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.inline-btn {
  min-height: 28px;
  padding: 0 10px;
  white-space: nowrap;
}

.flow-panel {
  display: grid;
  gap: 14px;
  padding: 14px;
  margin-top: 16px;
  border: 1px solid #edf1f6;
  border-radius: 8px;
  background: #ffffff;
}

.flow-panel-head,
.flow-panel-title,
.monitor-meta,
.monitor-event-head {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.flow-panel-head {
  align-items: center;
  justify-content: space-between;
}

.flow-panel-title {
  align-items: center;
  color: #17253d;
  font-weight: 800;
}

.monitor-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #8da0b8;
}

.monitor-dot--pulse {
  background: #2f6cf6;
  box-shadow: 0 0 0 0 rgba(47, 108, 246, 0.28);
  animation: pulse 1.6s ease-out infinite;
}

.monitor-meta,
.monitor-timeline-label,
.monitor-event-time {
  color: #7a8799;
  font-size: 12px;
}

.monitor-timeline,
.monitor-timeline-list,
.flow-copy,
.upload-item,
.candidate-main {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.monitor-event-copy,
.flow-text,
.candidate-summary,
.candidate-processing,
.empty-state,
.upload-note {
  line-height: 1.6;
}

.monitor-event {
  padding: 10px 12px;
  border-bottom: 1px solid #edf2f8;
}

.flow-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
  gap: 14px;
}

.flow-copy,
.flow-progress-card {
  display: grid;
  align-content: start;
  gap: 12px;
  min-height: 118px;
  padding: 14px;
  border: 1px solid #edf1f6;
  border-radius: 8px;
  background: #f7faff;
}

.flow-card-title {
  color: #40546f;
  font-size: 13px;
  font-weight: 800;
}

.flow-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #66758a;
  font-size: 13px;
}

.flow-status-row strong {
  color: #17253d;
  font-size: 16px;
  font-weight: 800;
  white-space: nowrap;
}

.flow-copy :deep(.el-progress-bar__outer),
.flow-progress-card :deep(.el-progress-bar__outer) {
  background-color: #e6ebf2;
}

.flow-copy :deep(.el-progress-bar__inner),
.flow-progress-card :deep(.el-progress-bar__inner) {
  background-color: #2f6cf6;
}

.flow-steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.flow-step {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr);
  gap: 10px;
  padding: 12px;
  border: 1px solid #edf1f6;
  border-radius: 8px;
  background: #ffffff;
}

.flow-step--active {
  border-color: #cfe0f8;
  background: #f7faff;
}

.flow-step--done {
  background: #f3faf7;
}

.flow-step-index {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: #eef3f9;
  color: #40546f;
  font-size: 13px;
  font-weight: 800;
}

.flow-step-title {
  color: #17253d;
  font-size: 13px;
  font-weight: 800;
}

.flow-step-copy {
  margin-top: 4px;
  color: #66758a;
  font-size: 12px;
  line-height: 1.5;
}

.info-banner,
.empty-state {
  padding: 12px;
  border-radius: 6px;
}

.info-banner {
  background: #eef7ff;
  color: #2568d8;
}

.upload-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: start;
}

.resume-upload {
  min-width: 0;
}

.resume-upload :deep(.el-upload) {
  width: 100%;
}

.resume-upload :deep(.el-upload-dragger) {
  display: grid;
  place-items: center;
  min-height: 156px;
  padding: 22px;
  border: 1px dashed #b9c9df;
  border-radius: 8px;
  background: #f7faff;
}

.resume-upload :deep(.el-upload-dragger:hover) {
  border-color: #2f6cf6;
  background: #f2f7ff;
}

.resume-upload__icon {
  color: #2f6cf6;
  font-size: 34px;
}

.resume-upload__text {
  margin-top: 8px;
  color: #17253d;
  font-size: 14px;
  font-weight: 800;
}

.resume-upload__tip {
  margin-top: 8px;
  color: #66758a;
  font-size: 12px;
}

.upload-list,
.candidate-list {
  display: grid;
  gap: 10px;
  margin-top: 14px;
  min-width: 0;
}

.upload-item,
.candidate-item {
  padding: 12px 0;
  border-bottom: 1px solid #edf2f8;
}

.upload-head {
  align-items: flex-start;
}

.upload-head strong,
.candidate-head strong {
  display: block;
  max-width: 100%;
  overflow: hidden;
  color: #17253d;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-meta,
.candidate-meta,
.candidate-summary,
.candidate-processing,
.upload-note {
  font-size: 13px;
}

.upload-step-chip,
.tag-chip {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0 8px;
  border-radius: 999px;
  background: #f1f4f8;
  color: #65758b;
  font-size: 12px;
  font-weight: 700;
}

.upload-step-chip--running {
  background: #eaf2ff;
  color: #2568d8;
}

.upload-step-chip--succeeded {
  background: #eaf8f1;
  color: #23845d;
}

.upload-step-chip--failed {
  background: #fff0f0;
  color: #c24141;
}

.candidate-item {
  align-items: flex-start;
}

.candidate-main {
  flex: 1;
}

.candidate-head {
  align-items: flex-start;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.empty-state {
  background: #f7f9fc;
}

@media (max-width: 1180px) {
  .task-detail-grid,
  .flow-summary,
  .flow-steps {
    grid-template-columns: 1fr;
  }

  .upload-actions {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .page-head,
  .panel-head,
  .upload-head,
  .upload-footer,
  .candidate-head,
  .candidate-item {
    align-items: flex-start;
    flex-direction: column;
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(47, 108, 246, 0.28);
  }

  70% {
    box-shadow: 0 0 0 10px rgba(47, 108, 246, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(47, 108, 246, 0);
  }
}
</style>
