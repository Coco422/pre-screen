import { describe, expect, it } from "vitest";

import {
  buildCandidateActionKeys,
  buildCandidateRiskItems,
  buildCandidateSignal,
  describeScoreBand,
  describeUploadStage,
  summarizeRiskSummary,
  summarizeTaskFlow
} from "./adminUi";

describe("admin UI helpers", () => {
  it("maps queued uploads into an intake stage", () => {
    expect(
      describeUploadStage({
        id: "u-1",
        fileName: "resume.pdf",
        status: "queued",
        progress: 0,
        createdAt: "2026-04-21T09:00:00Z",
        updatedAt: "2026-04-21T09:00:00Z"
      })
    ).toMatchObject({
      label: "排队接收",
      tone: "info",
      progress: 8
    });
  });

  it("prefers structured processing stages when AI enrichment is still running", () => {
    expect(
      describeUploadStage({
        id: "u-1",
        fileName: "resume.pdf",
        status: "parsing",
        progress: 35,
        createdAt: "2026-04-21T09:00:00Z",
        updatedAt: "2026-04-21T09:02:00Z",
        processing: {
          stage: "project_extract",
          status: "running",
          progress: 74,
          message: "正在整理项目经历、出题焦点与推荐语言。",
          steps: {
            upload: { label: "接收 PDF", status: "succeeded" },
            pdf_parse: { label: "提取文本层", status: "succeeded" },
            project_extract: { label: "整理项目经历", status: "running" },
            paper_generate: { label: "生成项目相关考卷", status: "pending" },
            paper_publish: { label: "发布考试入口", status: "pending" }
          }
        }
      })
    ).toMatchObject({
      label: "整理项目经历",
      detail: "正在整理项目经历、出题焦点与推荐语言。",
      tone: "info",
      progress: 74
    });
  });

  it("summarizes active task flow with a current system action", () => {
    expect(
      summarizeTaskFlow([
        {
          id: "u-1",
          fileName: "a.pdf",
          status: "queued",
          progress: 0,
          createdAt: "2026-04-21T09:00:00Z",
          updatedAt: "2026-04-21T09:00:00Z"
        },
        {
          id: "u-2",
          fileName: "b.pdf",
          status: "parsing",
          progress: 56,
          createdAt: "2026-04-21T09:00:00Z",
          updatedAt: "2026-04-21T09:01:00Z"
        }
      ])
    ).toMatchObject({
      label: "系统正在提取 1 份 PDF 文本",
      tone: "info",
      activeStep: 1
    });
  });

  it("builds candidate signals, risks, and recommendations from parse metrics", () => {
    const candidate = {
      id: "c-1",
      taskId: "t-1",
      name: "Ada",
      role: "Frontend Engineer",
      email: "",
      city: "Shanghai",
      phone: "",
      status: "待发卷",
      quality: "中",
      skills: ["Vue"],
      hobbies: [],
      heightCm: null,
      weightKg: null,
      availableInDays: 45,
      projectSummary: "负责业务中台改版与组件设计。",
      projects: [],
      analysis: {
        focusTopics: [],
        strengths: [],
        risks: [],
        recommendedLanguages: [],
        missingFields: []
      },
      reviewNotes: ["检测到低文本覆盖页，已触发多模态兜底。"],
      parseMetrics: {
        firstPageCharacters: 78,
        multimodalPages: 2,
        confidence: "中"
      },
      paperId: null,
      invitationToken: null,
      resultId: null
    };

    expect(buildCandidateSignal(candidate)).toMatchObject({
      qualityScore: 42,
      qualityLabel: "需要复核",
      readinessLabel: "建议先补画像"
    });
    expect(buildCandidateRiskItems(candidate)).toHaveLength(5);
    expect(buildCandidateActionKeys(candidate)).toEqual(["edit", "publish", "follow_up"]);
  });

  it("formats result risk summaries into readable labels", () => {
    expect(
      summarizeRiskSummary({
        event_count: 3,
        event_types: {
          copy: 1,
          window_blur: 2
        }
      })
    ).toMatchObject({
      level: "medium",
      label: "需关注",
      total: 3,
      items: [
        { key: "window_blur", label: "切屏", count: 2, tone: "warning" },
        { key: "copy", label: "复制", count: 1, tone: "warning" }
      ]
    });
  });

  it("classifies score bands for result surfaces", () => {
    expect(describeScoreBand(88)).toMatchObject({
      label: "强推荐",
      tone: "success"
    });
    expect(describeScoreBand(59)).toMatchObject({
      label: "待复核",
      tone: "warning"
    });
  });
});
