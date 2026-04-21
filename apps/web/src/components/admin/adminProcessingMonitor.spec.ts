import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  ADMIN_PROCESSING_MONITOR_STORAGE_KEY,
  formatAdminProcessingMonitorSyncLabel,
  normalizeAdminProcessingMonitorSnapshot,
  readAdminProcessingMonitorSnapshot
} from "./adminProcessingMonitor";

describe("admin processing monitor helpers", () => {
  let storage: Record<string, string>;

  beforeEach(() => {
    storage = {};
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      value: {
        getItem(key: string) {
          return storage[key] ?? null;
        },
        setItem(key: string, value: string) {
          storage[key] = value;
        },
        removeItem(key: string) {
          delete storage[key];
        },
        clear() {
          storage = {};
        }
      }
    });
  });

  it("normalizes a nested task summary into a banner-ready snapshot", () => {
    expect(
      normalizeAdminProcessingMonitorSnapshot({
        taskId: "task-42",
        taskTitle: "春招前端专场",
        taskLink: "/admin/tasks/task-42",
        label: "系统正在解析简历",
        activeUploadCount: 3,
        isProcessing: true,
        lastSyncedAt: "2026-04-21T09:10:00.000Z"
      })
    ).toMatchObject({
      taskId: "task-42",
      taskTitle: "春招前端专场",
      label: "系统正在解析简历",
      activeUploadCount: 3,
      processing: true,
      detailHref: "/admin/tasks/task-42",
      lastSyncedAt: "2026-04-21T09:10:00.000Z"
    });
  });

  it("hides the banner when there is no active processing task", () => {
    expect(
      normalizeAdminProcessingMonitorSnapshot({
        taskId: "task-12",
        taskTitle: "已完成批次",
        taskLink: "/admin/tasks/task-12",
        activeUploadCount: 0,
        isProcessing: false
      })
    ).toBeNull();
    expect(
      normalizeAdminProcessingMonitorSnapshot({
        taskId: "task-77",
        activeUploadCount: 2,
        isProcessing: true
      })
    ).toBeNull();
  });

  it("reads and validates the monitor snapshot from localStorage", () => {
    window.localStorage.setItem(
      ADMIN_PROCESSING_MONITOR_STORAGE_KEY,
      JSON.stringify({
        taskId: "task-51",
        taskTitle: "校招算法批次",
        taskLink: "/admin/tasks/task-51",
        label: "系统正在解析 1 份 PDF",
        activeUploadCount: 1,
        isProcessing: true,
        lastSyncedAt: "2026-04-21T09:15:00.000Z"
      })
    );

    expect(readAdminProcessingMonitorSnapshot()).toMatchObject({
      taskId: "task-51",
      taskTitle: "校招算法批次",
      detailHref: "/admin/tasks/task-51"
    });
  });

  it("suppresses recent finished states that are no longer processing", () => {
    window.localStorage.setItem(
      ADMIN_PROCESSING_MONITOR_STORAGE_KEY,
      JSON.stringify({
        taskId: "task-63",
        taskTitle: "已完成批次",
        taskLink: "/admin/tasks/task-63",
        label: "全部解析完成",
        activeUploadCount: 0,
        isProcessing: false,
        lastSyncedAt: "2026-04-21T09:18:00.000Z"
      })
    );

    expect(readAdminProcessingMonitorSnapshot(new Date("2026-04-21T09:19:00.000Z"))).toBeNull();
  });

  it("formats sync labels into short status copy", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-04-21T09:20:00.000Z"));

    expect(formatAdminProcessingMonitorSyncLabel("2026-04-21T09:19:40.000Z")).toBe("刚刚同步");
    expect(formatAdminProcessingMonitorSyncLabel("2026-04-21T09:17:00.000Z")).toBe("3 分钟前同步");
    expect(formatAdminProcessingMonitorSyncLabel("invalid-date")).toBe("等待同步");

    vi.useRealTimers();
  });
});
