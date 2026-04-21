import type { CandidateDetail, ParseJobSummary } from "../../lib/gateway";

export type AdminTone = "neutral" | "info" | "success" | "warning" | "danger";

export type UploadStageDescriptor = {
  label: string;
  detail: string;
  tone: AdminTone;
  progress: number;
};

export type TaskFlowSummary = {
  label: string;
  detail: string;
  tone: AdminTone;
  progress: number;
  activeStep: number;
};

export type CandidateSignalSummary = {
  qualityScore: number;
  qualityLabel: string;
  readinessLabel: string;
  tone: AdminTone;
};

export type CandidateRiskItem = {
  label: string;
  detail: string;
  tone: AdminTone;
};

export type CandidateActionKey = "publish" | "edit" | "follow_up" | "view_result" | "view_entry";

export type ScoreBandDescriptor = {
  label: string;
  detail: string;
  tone: AdminTone;
};

export type RiskSummaryItem = {
  key: string;
  label: string;
  count: number;
  tone: AdminTone;
};

export type RiskSummaryDescriptor = {
  total: number;
  label: string;
  level: "low" | "medium" | "high";
  tone: AdminTone;
  items: RiskSummaryItem[];
};

const uploadStatusProgress = {
  queued: 8,
  parsing: 55,
  parsed: 100,
  failed: 100
} as const;

const processingStageMeta = {
  uploaded: {
    key: "queued",
    label: "排队接收",
    detail: "系统已收下文件，正在创建候选人占位并排队解析。",
    tone: "info",
    progress: 8,
    activeStep: 0
  },
  parsing_pdf: {
    key: "pdf_parse",
    label: "提取 PDF 文本",
    detail: "系统正在读取 PDF 文本层，并在低文本页触发多模态兜底。",
    tone: "info",
    progress: 42,
    activeStep: 1
  },
  project_extract: {
    key: "project_extract",
    label: "整理项目经历",
    detail: "系统正在整理项目经历、出题焦点与推荐语言。",
    tone: "info",
    progress: 74,
    activeStep: 2
  },
  profile_ready: {
    key: "ready",
    label: "解析完成",
    detail: "候选人画像已生成，可以继续发卷。",
    tone: "success",
    progress: 100,
    activeStep: 3
  },
  paper_ready: {
    key: "paper_ready",
    label: "考卷草稿已生成",
    detail: "候选人画像已完成，系统已生成项目相关考卷草稿。",
    tone: "success",
    progress: 100,
    activeStep: 3
  },
  published: {
    key: "published",
    label: "考试入口已发布",
    detail: "链接与验证码已生成，可发送给候选人。",
    tone: "success",
    progress: 100,
    activeStep: 3
  },
  failed: {
    key: "failed",
    label: "解析失败",
    detail: "系统无法完成当前 PDF 解析，建议重新上传或人工处理。",
    tone: "danger",
    progress: 100,
    activeStep: 3
  }
} as const satisfies Record<
  string,
  {
    key: string;
    label: string;
    detail: string;
    tone: AdminTone;
    progress: number;
    activeStep: number;
  }
>;

const riskEventLabels: Record<string, string> = {
  window_blur: "切屏",
  page_hidden: "离开页面",
  copy: "复制",
  paste: "粘贴",
  network_offline: "网络中断",
  network_online: "网络恢复"
};

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function normalizePercent(value: number, fallback: number) {
  const safeValue = Number.isFinite(value) ? value : fallback;
  return clamp(Math.round(safeValue), 0, 100);
}

function qualityBaseScore(quality: string) {
  if (quality === "高") {
    return 86;
  }
  if (quality === "中") {
    return 66;
  }
  if (quality === "低") {
    return 38;
  }
  return 18;
}

function resolveProcessingStage(upload: ParseJobSummary) {
  const stage = upload.processing?.stage;
  if (stage && stage in processingStageMeta) {
    return processingStageMeta[stage as keyof typeof processingStageMeta];
  }
  if (upload.status === "queued") {
    return processingStageMeta.uploaded;
  }
  if (upload.status === "parsing") {
    return processingStageMeta.parsing_pdf;
  }
  if (upload.status === "parsed") {
    return processingStageMeta.profile_ready;
  }
  if (upload.status === "failed") {
    return processingStageMeta.failed;
  }
  return null;
}

export function describeUploadStage(upload: ParseJobSummary): UploadStageDescriptor {
  const processingStage = resolveProcessingStage(upload);
  if (processingStage && upload.processing) {
    return {
      label: processingStage.label,
      detail: upload.processing.message || processingStage.detail,
      tone: processingStage.tone,
      progress: normalizePercent(upload.processing.progress, processingStage.progress)
    };
  }

  if (upload.status === "queued") {
    return {
      label: "排队接收",
      detail: "系统已收下文件，正在创建候选人占位并排队解析。",
      tone: "info",
      progress: Math.max(normalizePercent(upload.progress, uploadStatusProgress.queued), uploadStatusProgress.queued)
    };
  }

  if (upload.status === "parsing") {
    const parsingProgress = normalizePercent(upload.progress, uploadStatusProgress.parsing);
    const parsingLabel = parsingProgress >= 60 ? "整理画像" : "提取文本";
    return {
      label: parsingLabel,
      detail:
        parsingProgress >= 60
          ? "系统正在整理技能、联系方式与项目摘要。"
          : "系统正在读取 PDF 文本层，并在低文本页触发多模态兜底。",
      tone: "info",
      progress: parsingProgress
    };
  }

  if (upload.status === "parsed") {
    return {
      label: "解析完成",
      detail: upload.candidateId ? "候选人画像已生成，可以继续发卷。" : "解析完成，等待同步候选人画像。",
      tone: "success",
      progress: 100
    };
  }

  if (upload.status === "failed") {
    return {
      label: "解析失败",
      detail: "系统无法完成当前 PDF 解析，建议重新上传或人工处理。",
      tone: "danger",
      progress: 100
    };
  }

  return {
    label: upload.status,
    detail: "当前状态由后端返回。",
    tone: "neutral",
    progress: normalizePercent(upload.progress, 0)
  };
}

export function summarizeTaskFlow(uploads: ParseJobSummary[]): TaskFlowSummary {
  if (!uploads.length) {
    return {
      label: "等待上传 PDF",
      detail: "上传后会自动创建候选人占位，并持续刷新解析进度。",
      tone: "neutral",
      progress: 0,
      activeStep: 0
    };
  }

  const stageCounts = uploads.reduce(
    (accumulator, upload) => {
      const stage = resolveProcessingStage(upload)?.key ?? "queued";
      accumulator[stage as keyof typeof accumulator] += 1;
      return accumulator;
    },
    {
      queued: 0,
      pdf_parse: 0,
      project_extract: 0,
      ready: 0,
      paper_ready: 0,
      published: 0,
      failed: 0
    }
  );
  const averageProgress = normalizePercent(
    uploads.reduce((total, upload) => total + describeUploadStage(upload).progress, 0) / uploads.length,
    0
  );

  if (stageCounts.project_extract > 0) {
    return {
      label: `系统正在整理 ${stageCounts.project_extract} 份候选人画像`,
      detail:
        stageCounts.pdf_parse > 0
          ? `另有 ${stageCounts.pdf_parse} 份还在提取 PDF 文本层，系统会持续更新。`
          : stageCounts.queued > 0
            ? `还有 ${stageCounts.queued} 份刚入队，当前批次会自动继续处理。`
            : "系统正在整理项目经历、出题焦点与推荐语言。",
      tone: "info",
      progress: averageProgress,
      activeStep: 2
    };
  }

  if (stageCounts.pdf_parse > 0) {
    return {
      label: `系统正在提取 ${stageCounts.pdf_parse} 份 PDF 文本`,
      detail:
        stageCounts.queued > 0
          ? `还有 ${stageCounts.queued} 份在排队，文本提取后会自动进入项目整理。`
          : "系统正在读取 PDF 文本层，并在低文本页触发多模态兜底。",
      tone: "info",
      progress: averageProgress,
      activeStep: 1
    };
  }

  if (stageCounts.queued > 0) {
    return {
      label: `已有 ${stageCounts.queued} 份 PDF 进入队列`,
      detail: "系统正在登记文件并创建候选人占位。",
      tone: "info",
      progress: averageProgress,
      activeStep: 0
    };
  }

  const completedCount = stageCounts.ready + stageCounts.paper_ready + stageCounts.published;

  if (stageCounts.failed > 0 && completedCount === 0) {
    return {
      label: "本批次解析失败",
      detail: "建议重新上传失败文件，或先处理异常候选人。",
      tone: "danger",
      progress: averageProgress,
      activeStep: 3
    };
  }

  if (stageCounts.failed > 0) {
    return {
      label: `${completedCount} 份已完成，${stageCounts.failed} 份异常`,
      detail: "优先处理失败文件，其余候选人已可继续发卷。",
      tone: "warning",
      progress: averageProgress,
      activeStep: 3
    };
  }

  return {
    label: `全部 ${completedCount} 份 PDF 已完成解析`,
    detail: "候选人画像已就绪，可以继续筛选和发布考试入口。",
    tone: "success",
    progress: 100,
    activeStep: 3
  };
}

export function buildCandidateSignal(candidate: CandidateDetail): CandidateSignalSummary {
  let qualityScore = qualityBaseScore(candidate.quality || candidate.parseMetrics.confidence);

  if (candidate.parseMetrics.firstPageCharacters >= 220) {
    qualityScore += 6;
  } else if (candidate.parseMetrics.firstPageCharacters < 90) {
    qualityScore -= 6;
  }

  if (candidate.parseMetrics.multimodalPages === 0) {
    qualityScore += 4;
  } else if (candidate.parseMetrics.multimodalPages >= 2) {
    qualityScore -= 12;
  } else {
    qualityScore -= 4;
  }

  if (!candidate.email) {
    qualityScore -= 3;
  }
  if (!candidate.phone) {
    qualityScore -= 3;
  }

  qualityScore = clamp(Math.round(qualityScore), 0, 100);

  if (qualityScore >= 78) {
    return {
      qualityScore,
      qualityLabel: "可直接推进",
      readinessLabel: "建议进入发卷",
      tone: "success"
    };
  }

  if (qualityScore >= 40) {
    return {
      qualityScore,
      qualityLabel: "需要复核",
      readinessLabel: "建议先补画像",
      tone: "warning"
    };
  }

  return {
    qualityScore,
    qualityLabel: "信息不完整",
    readinessLabel: "建议人工确认",
    tone: "danger"
  };
}

export function buildCandidateRiskItems(candidate: CandidateDetail): CandidateRiskItem[] {
  const items: CandidateRiskItem[] = [];

  if (candidate.parseMetrics.multimodalPages >= 2) {
    items.push({
      label: "多页需要兜底识别",
      detail: `共 ${candidate.parseMetrics.multimodalPages} 页触发多模态补读，建议抽样复核正文准确性。`,
      tone: "danger"
    });
  } else if (candidate.parseMetrics.multimodalPages === 1) {
    items.push({
      label: "存在补读页",
      detail: "检测到 1 页低文本覆盖，建议关注关键经历和联系方式。",
      tone: "warning"
    });
  }

  if (candidate.parseMetrics.firstPageCharacters < 120) {
    items.push({
      label: "首页文本偏少",
      detail: `首页仅抽取 ${candidate.parseMetrics.firstPageCharacters} 个字符，可能影响摘要质量。`,
      tone: "warning"
    });
  }

  if (!candidate.email) {
    items.push({
      label: "邮箱缺失",
      detail: "简历未提取到邮箱，后续通知链路可能中断。",
      tone: "warning"
    });
  }

  if (!candidate.phone) {
    items.push({
      label: "手机号缺失",
      detail: "建议人工补齐电话，避免只靠邮箱触达。",
      tone: "warning"
    });
  }

  if ((candidate.availableInDays ?? 0) > 30) {
    items.push({
      label: "到岗周期较长",
      detail: `当前预计 ${candidate.availableInDays} 天到岗，建议提前校准招聘节奏。`,
      tone: "info"
    });
  }

  return items;
}

export function buildCandidateActionKeys(candidate: CandidateDetail): CandidateActionKey[] {
  const actions: CandidateActionKey[] = [];
  const signal = buildCandidateSignal(candidate);

  if (candidate.resultId) {
    actions.push("view_result");
  }

  if (signal.qualityScore < 60 || !candidate.email || !candidate.phone) {
    actions.push("edit");
  }

  if (candidate.paperId && candidate.invitationToken) {
    actions.push("view_entry");
  } else if (candidate.status !== "解析中" && candidate.quality !== "待解析") {
    actions.push("publish");
  }

  if (!candidate.resultId) {
    actions.push("follow_up");
  }

  return Array.from(new Set(actions));
}

export function summarizeRiskSummary(riskSummary: Record<string, unknown>): RiskSummaryDescriptor {
  const rawTotal = typeof riskSummary.event_count === "number" ? riskSummary.event_count : 0;
  const rawTypes =
    riskSummary.event_types && typeof riskSummary.event_types === "object"
      ? (riskSummary.event_types as Record<string, unknown>)
      : {};

  const items = Object.entries(rawTypes)
    .map(([key, value]) => ({
      key,
      label: riskEventLabels[key] ?? key,
      count: typeof value === "number" ? value : 0,
      tone: key === "copy" || key === "paste" || key === "window_blur" ? ("warning" as const) : ("info" as const)
    }))
    .filter((item) => item.count > 0)
    .sort((left, right) => right.count - left.count);

  if (rawTotal >= 6) {
    return {
      total: rawTotal,
      label: "高风险",
      level: "high",
      tone: "danger",
      items
    };
  }

  if (rawTotal >= 2) {
    return {
      total: rawTotal,
      label: "需关注",
      level: "medium",
      tone: "warning",
      items
    };
  }

  return {
    total: rawTotal,
    label: rawTotal ? "低风险" : "未见异常",
    level: "low",
    tone: rawTotal ? "info" : "success",
    items
  };
}

export function describeScoreBand(score: number): ScoreBandDescriptor {
  if (score >= 80) {
    return {
      label: "强推荐",
      detail: "答题表现稳定，可以优先进入下一轮。",
      tone: "success"
    };
  }

  if (score >= 60) {
    return {
      label: "可继续评估",
      detail: "整体通过，但建议结合主观题和风险事件再判断。",
      tone: "info"
    };
  }

  return {
    label: "待复核",
    detail: "分数偏低，建议结合作答细节与风险摘要人工复核。",
    tone: "warning"
  };
}
