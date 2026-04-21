import { beforeEach, describe, expect, it } from "vitest";

import { buildTaskMonitorState, readActiveTaskMonitor, readTaskMonitor, writeTaskMonitor } from "./taskMonitor";

describe("task monitor helpers", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("builds a refresh-safe monitor snapshot for active uploads", () => {
    const state = buildTaskMonitorState({
      taskId: "t-001",
      taskTitle: "前端技术筛选",
      uploads: [
        {
          id: "u-1",
          fileName: "resume.pdf",
          status: "parsing",
          progress: 35,
          createdAt: "2026-04-21T09:00:00Z",
          updatedAt: "2026-04-21T09:01:00Z",
          processing: {
            stage: "project_extract",
            status: "running",
            progress: 74,
            message: "文本层已提取，正在整理项目经历与推荐语言。",
            steps: {
              upload: { label: "接收 PDF", status: "succeeded" },
              pdf_parse: { label: "提取文本层", status: "succeeded" },
              project_extract: { label: "整理项目经历", status: "running" },
              paper_generate: { label: "生成项目相关考卷", status: "pending" },
              paper_publish: { label: "发布考试入口", status: "pending" }
            }
          }
        }
      ],
      now: new Date("2026-04-21T09:02:00Z"),
      pollingIntervalMs: 1_200
    });

    expect(state.isProcessing).toBe(true);
    expect(state.activeUploadCount).toBe(1);
    expect(state.label).toBe("系统正在整理 1 份候选人画像");
    expect(state.events[0]).toMatchObject({
      label: "resume.pdf 已开始 整理项目经历",
      tone: "info"
    });
  });

  it("persists and reloads the active monitor snapshot", () => {
    const state = buildTaskMonitorState({
      taskId: "t-001",
      taskTitle: "前端技术筛选",
      uploads: [],
      now: new Date("2026-04-21T09:02:00Z")
    });

    writeTaskMonitor(state);

    expect(readTaskMonitor("t-001")?.taskTitle).toBe("前端技术筛选");
    expect(readActiveTaskMonitor(new Date("2026-04-21T09:03:00Z"))?.taskId).toBe("t-001");
  });
});
