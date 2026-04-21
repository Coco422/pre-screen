import type { ParseJobSummary } from "../../lib/gateway";
import { buildTaskDetailPath } from "./adminRouting";
import { describeUploadStage, summarizeTaskFlow, type AdminTone } from "./adminUi";

const TASK_MONITOR_STORAGE_PREFIX = "pre-screen:admin-monitor:";
export const ACTIVE_TASK_MONITOR_STORAGE_KEY = "pre-screen:admin-monitor:active";
const MAX_MONITOR_EVENTS = 10;
const RECENT_FINISH_WINDOW_MS = 3 * 60 * 1000;

type StoredUploadStage = {
  fingerprint: string;
  label: string;
  detail: string;
  progress: number;
};

export type TaskMonitorEvent = {
  id: string;
  uploadId: string;
  fileName: string;
  label: string;
  detail: string;
  tone: AdminTone;
  progress: number;
  at: string;
};

export type TaskMonitorState = {
  taskId: string;
  taskTitle: string;
  taskLink: string;
  label: string;
  detail: string;
  tone: AdminTone;
  progress: number;
  activeStep: number;
  activeUploadCount: number;
  isProcessing: boolean;
  lastSyncedAt: string;
  nextPollAt: string | null;
  uploads: Record<string, StoredUploadStage>;
  events: TaskMonitorEvent[];
};

type BuildTaskMonitorOptions = {
  taskId: string;
  taskTitle: string;
  uploads: ParseJobSummary[];
  previous?: TaskMonitorState | null;
  now?: Date;
  pollingIntervalMs?: number;
};

function isActiveUpload(upload: ParseJobSummary) {
  const stage = upload.processing?.stage;
  if (stage === "profile_ready" || stage === "paper_ready" || stage === "published" || stage === "failed") {
    return false;
  }
  return upload.status !== "parsed" && upload.status !== "failed";
}

function buildUploadFingerprint(upload: ParseJobSummary, label: string, detail: string) {
  return [
    upload.status,
    upload.progress,
    upload.processing?.stage ?? "",
    upload.processing?.status ?? "",
    upload.processing?.progress ?? "",
    label,
    detail
  ].join("|");
}

function monitorStorageKey(taskId: string) {
  return `${TASK_MONITOR_STORAGE_PREFIX}${taskId}`;
}

function safeParseMonitor(raw: string | null): TaskMonitorState | null {
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as TaskMonitorState;
  } catch {
    return null;
  }
}

export function buildTaskMonitorState({
  taskId,
  taskTitle,
  uploads,
  previous,
  now = new Date(),
  pollingIntervalMs = 0
}: BuildTaskMonitorOptions): TaskMonitorState {
  const flow = summarizeTaskFlow(uploads);
  const nextEvents: TaskMonitorEvent[] = [];
  const storedUploads: Record<string, StoredUploadStage> = {};

  for (const upload of uploads) {
    const stage = describeUploadStage(upload);
    const fingerprint = buildUploadFingerprint(upload, stage.label, stage.detail);
    const previousUpload = previous?.uploads?.[upload.id];
    storedUploads[upload.id] = {
      fingerprint,
      label: stage.label,
      detail: stage.detail,
      progress: stage.progress
    };

    const stageChanged = previousUpload && previousUpload.fingerprint !== fingerprint;
    const bootstrapActiveUpload = !previousUpload && isActiveUpload(upload);
    if (!stageChanged && !bootstrapActiveUpload) {
      continue;
    }

    const transitionLabel = stageChanged ? `${upload.fileName} 进入 ${stage.label}` : `${upload.fileName} 已开始 ${stage.label}`;
    nextEvents.push({
      id: `${upload.id}:${now.toISOString()}:${stage.label}`,
      uploadId: upload.id,
      fileName: upload.fileName,
      label: transitionLabel,
      detail: stage.detail,
      tone: stage.tone,
      progress: stage.progress,
      at: now.toISOString()
    });
  }

  const isProcessing = uploads.some(isActiveUpload);
  const mergedEvents = [...nextEvents, ...(previous?.events ?? [])]
    .sort((left, right) => Date.parse(right.at) - Date.parse(left.at))
    .slice(0, MAX_MONITOR_EVENTS);

  return {
    taskId,
    taskTitle,
    taskLink: buildTaskDetailPath(taskId),
    label: flow.label,
    detail: flow.detail,
    tone: flow.tone,
    progress: flow.progress,
    activeStep: flow.activeStep,
    activeUploadCount: uploads.filter(isActiveUpload).length,
    isProcessing,
    lastSyncedAt: now.toISOString(),
    nextPollAt: isProcessing && pollingIntervalMs > 0 ? new Date(now.getTime() + pollingIntervalMs).toISOString() : null,
    uploads: storedUploads,
    events: mergedEvents
  };
}

export function readTaskMonitor(taskId: string): TaskMonitorState | null {
  if (typeof window === "undefined") {
    return null;
  }
  return safeParseMonitor(window.localStorage.getItem(monitorStorageKey(taskId)));
}

export function writeTaskMonitor(state: TaskMonitorState) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(monitorStorageKey(state.taskId), JSON.stringify(state));
  window.localStorage.setItem(ACTIVE_TASK_MONITOR_STORAGE_KEY, JSON.stringify(state));
}

export function readActiveTaskMonitor(now = new Date()): TaskMonitorState | null {
  if (typeof window === "undefined") {
    return null;
  }
  const monitor = safeParseMonitor(window.localStorage.getItem(ACTIVE_TASK_MONITOR_STORAGE_KEY));
  if (!monitor) {
    return null;
  }
  if (monitor.isProcessing) {
    return monitor;
  }
  return Date.parse(monitor.lastSyncedAt) + RECENT_FINISH_WINDOW_MS >= now.getTime() ? monitor : null;
}
