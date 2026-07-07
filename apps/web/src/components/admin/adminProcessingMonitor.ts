import {
  ACTIVE_TASK_MONITOR_STORAGE_KEY,
  readActiveTaskMonitor,
  type TaskMonitorState
} from "./taskMonitor";

export const ADMIN_PROCESSING_MONITOR_STORAGE_KEY = ACTIVE_TASK_MONITOR_STORAGE_KEY;

export type AdminProcessingMonitorSnapshot = {
  taskId: string;
  taskTitle: string;
  label: string;
  activeUploadCount: number;
  lastSyncedAt: string | null;
  processing: boolean;
  detailHref: string;
};

type TaskMonitorSummaryLike = Pick<
  TaskMonitorState,
  "taskId" | "taskTitle" | "taskLink" | "label" | "activeUploadCount" | "isProcessing" | "lastSyncedAt"
>;

function isTaskMonitorSummaryLike(value: unknown): value is TaskMonitorSummaryLike {
  return typeof value === "object" && value !== null;
}

export function normalizeAdminProcessingMonitorSnapshot(rawValue: unknown): AdminProcessingMonitorSnapshot | null {
  if (!isTaskMonitorSummaryLike(rawValue)) {
    return null;
  }

  if (!rawValue.taskTitle || !rawValue.taskLink) {
    return null;
  }

  if (!rawValue.isProcessing && rawValue.activeUploadCount <= 0) {
    return null;
  }

  return {
    taskId: rawValue.taskId,
    taskTitle: rawValue.taskTitle,
    label: rawValue.label || "系统正在处理",
    activeUploadCount: Math.max(0, Math.round(rawValue.activeUploadCount || 0)),
    lastSyncedAt: rawValue.lastSyncedAt || null,
    processing: rawValue.isProcessing,
    detailHref: rawValue.taskLink
  };
}

export function readAdminProcessingMonitorSnapshot(now = new Date()): AdminProcessingMonitorSnapshot | null {
  return normalizeAdminProcessingMonitorSnapshot(readActiveTaskMonitor(now));
}

export function formatAdminProcessingMonitorSyncLabel(lastSyncedAt: string | null, now = Date.now()): string {
  if (!lastSyncedAt) {
    return "等待同步";
  }

  const syncedAt = new Date(lastSyncedAt).getTime();
  if (Number.isNaN(syncedAt)) {
    return "等待同步";
  }

  const diffMs = Math.max(0, now - syncedAt);
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffMs < 90000) {
    return "刚刚同步";
  }

  if (diffMinutes < 60) {
    return `${diffMinutes} 分钟前同步`;
  }

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours} 小时前同步`;
  }

  const date = new Date(syncedAt);
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  return `${month}/${day} ${hours}:${minutes}`;
}
