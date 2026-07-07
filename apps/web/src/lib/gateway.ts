const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";

export type CandidateCard = {
  id: string;
  name: string;
  role: string;
  city: string;
  status: string;
  quality: string;
  summary: string;
  skills: string[];
};

export type CandidateDetail = {
  id: string;
  name: string;
  role: string;
  phone?: string | null;
  email: string | null;
  city: string;
  skills: string[];
  projectSummary: string;
  markdownPreview?: string;
  avatarUrl?: string | null;
  parseMetrics: {
    firstPageCharacters: number;
    multimodalPages: number;
    confidence: string;
  };
  reviewNotes: string[];
  nextActions: Array<{ label: string; target: string }>;
};

export type BatchAnalysis = {
  batchId: string | null;
  outputDir?: string;
  analysisMarkdown: string;
};

export type PaperDraft = {
  paperId: string;
  title: string;
  mix: Record<string, number>;
  questions: Array<{
    type: string;
    title: string;
    score: number;
    description: string;
  }>;
};

export type ExamQuestion = {
  id: string;
  kind: "base_info" | "objective" | "subjective" | "coding";
  shortLabel: string;
  typeLabel: string;
  title: string;
  description: string;
  score: number;
  fields?: string[];
  options?: string[];
  language?: string;
  supportedLanguages?: string[];
  starterCode?: string;
};

export type ExamShellPayload = {
  token: string;
  paperTitle: string;
  durationMinutes: number;
  heartbeatIntervalMs: number;
  autosaveIntervalMs: number;
  riskEvents: string[];
  questions: ExamQuestion[];
};

export type CodingRunResult = {
  mode: "run";
  stdout: string;
  stderr?: string | null;
  compile_output?: string | null;
  status?: { id?: number; description?: string };
};

export type CodingSubmitResult = {
  mode: "submit";
  question_id: string;
  results: Array<{
    stdin: string;
    expected_stdout: string;
    actual_stdout: string;
    score: number;
    passed: boolean;
    status?: { id?: number; description?: string };
  }>;
  summary: {
    passed_count: number;
    failed_count: number;
    total_score: number;
    max_score: number;
  };
};

const candidateFallback: CandidateCard[] = [
  {
    id: "c-001",
    name: "郭子贤",
    role: "全栈开发工程师",
    city: "深圳",
    status: "待发卷",
    quality: "高",
    summary: "简历文本层完整，系统已提取邮箱、技能与项目亮点，建议直接生成考卷草稿。",
    skills: ["Python", "C++", "Vue"]
  },
  {
    id: "c-002",
    name: "梁承与",
    role: "前端实习生",
    city: "广州",
    status: "待审核",
    quality: "中",
    summary: "第二页低文本覆盖，已触发多模态补读，建议 HR 先检查项目细节后发卷。",
    skills: ["Vue", "TypeScript", "工程化"]
  },
  {
    id: "c-003",
    name: "沈昊天",
    role: "前端开发工程师",
    city: "深圳",
    status: "已开考",
    quality: "高",
    summary: "候选人已进入考试会话，自动保存与心跳正常，暂无异常事件。",
    skills: ["JavaScript", "Vue", "浏览器"]
  }
];

const candidateDetailFallback: CandidateDetail = {
  id: "c-001",
  name: "郭子贤",
  role: "全栈开发工程师",
  phone: "150****0619",
  email: "15099970619@163.com",
  city: "深圳",
  skills: ["Python", "Java", "C++", "Vue"],
  projectSummary: "做过权限管理、接口编排和前后端联调，整体表达清晰，技术栈跨度较大。",
  markdownPreview: "暂无真实 Markdown。上传并解析简历后，这里会展示页序保真的 Markdown 预览。",
  avatarUrl: null,
  parseMetrics: {
    firstPageCharacters: 1740,
    multimodalPages: 1,
    confidence: "高"
  },
  reviewNotes: ["第 2 页低文本覆盖，已触发多模态补读。", "基础信息字段完整，暂无人工修正。"],
  nextActions: [
    { label: "生成考卷草稿", target: "/admin/papers/p-001" },
    { label: "修正候选人画像", target: "/admin/candidates/c-001/edit" }
  ]
};

const paperDraftFallback: PaperDraft = {
  paperId: "p-001",
  title: "前端实习生考卷草稿",
  mix: {
    base_info: 1,
    objective: 4,
    subjective: 2,
    coding: 1
  },
  questions: [
    { type: "基础信息", title: "补充基础信息", score: 0, description: "填写身高、体重、爱好和可到岗时间。" },
    { type: "客观题", title: "Vue 响应式原理基础", score: 5, description: "根据候选人简历中的 Vue 信号优先保留。" },
    { type: "客观题", title: "TypeScript 类型系统", score: 5, description: "覆盖联合类型、泛型和类型收窄。" },
    { type: "主观题", title: "请复盘一个你最熟悉的项目", score: 15, description: "聚焦完整度、角色边界和复盘深度。" },
    { type: "代码题", title: "实现一个数组去重函数", score: 50, description: "支持多语言，后续将接 Judge Bridge 判题。" }
  ]
};

const examShellFallback: ExamShellPayload = {
  token: "token-demo",
  paperTitle: "技术岗在线考核",
  durationMinutes: 90,
  heartbeatIntervalMs: 15000,
  autosaveIntervalMs: 1200,
  riskEvents: ["window_blur", "page_hidden", "copy", "paste", "network_offline", "network_online"],
  questions: [
    {
      id: "q-base-1",
      kind: "base_info",
      shortLabel: "基础信息",
      typeLabel: "基础信息",
      title: "补充基础信息",
      description: "请补全个人基础信息，方便 HR 结合岗位需求做后续沟通。",
      score: 0,
      fields: ["身高", "体重", "爱好", "可到岗时间"]
    },
    {
      id: "q-obj-1",
      kind: "objective",
      shortLabel: "客观题 1",
      typeLabel: "客观题",
      title: "Vue 响应式原理基础",
      description: "请选出最符合 Vue 响应式更新机制的描述。",
      score: 5,
      options: ["Proxy 劫持并按依赖触发更新", "通过轮询监听数据变化", "只依赖模板字符串解析"]
    },
    {
      id: "q-sub-1",
      kind: "subjective",
      shortLabel: "主观题",
      typeLabel: "主观题",
      title: "请复盘一个你最熟悉的项目",
      description: "重点讲清楚你的角色、最难的一段、以及如何验证结果。",
      score: 15
    },
    {
      id: "q-code-1",
      kind: "coding",
      shortLabel: "代码题",
      typeLabel: "代码题",
      title: "实现一个数组去重函数",
      description: "请从标准输入读取一个 JSON 数组，输出保持顺序稳定的去重结果，例如输入 [1,1,2,3,2] 输出 [1,2,3]。",
      score: 50,
      language: "JavaScript",
      supportedLanguages: ["C", "C++", "Java", "Python", "JavaScript", "TypeScript", "Go", "Rust"],
      starterCode: "function unique(items) {\n  return [...new Set(items)];\n}"
    }
  ]
};

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function apiUrl(path?: string | null): string | null {
  if (!path) {
    return null;
  }
  if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("data:")) {
    return path;
  }
  return `${API_BASE}${path}`;
}

async function requestJson<T>(path: string, init?: RequestInit, fallback?: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {})
      },
      ...init
    });
    if (!response.ok) {
      throw new Error(`Request failed with ${response.status}`);
    }
    return (await response.json()) as T;
  } catch (error) {
    if (fallback !== undefined) {
      return clone(fallback);
    }
    throw error;
  }
}

export async function loadCandidates(): Promise<CandidateCard[]> {
  const response = await requestJson<{ items: CandidateCard[] }>("/admin/candidates", undefined, {
    items: candidateFallback
  });
  return response.items;
}

export async function loadCandidateDetail(candidateId: string): Promise<CandidateDetail> {
  const response = await requestJson<{
    id: string;
    name: string;
    role: string;
    phone?: string | null;
    email: string | null;
    city: string;
    skills: string[];
    project_summary: string;
    markdown_preview?: string;
    avatar_url?: string | null;
    parse_metrics: {
      first_page_characters: number;
      multimodal_pages: number;
      confidence: string;
    };
    review_notes: string[];
    next_actions: Array<{ label: string; target: string }>;
  }>(`/admin/candidates/${candidateId}`, undefined, {
    id: candidateDetailFallback.id,
    name: candidateDetailFallback.name,
    role: candidateDetailFallback.role,
    phone: candidateDetailFallback.phone,
    email: candidateDetailFallback.email,
    city: candidateDetailFallback.city,
    skills: candidateDetailFallback.skills,
    project_summary: candidateDetailFallback.projectSummary,
    markdown_preview: candidateDetailFallback.markdownPreview,
    avatar_url: candidateDetailFallback.avatarUrl,
    parse_metrics: {
      first_page_characters: candidateDetailFallback.parseMetrics.firstPageCharacters,
      multimodal_pages: candidateDetailFallback.parseMetrics.multimodalPages,
      confidence: candidateDetailFallback.parseMetrics.confidence
    },
    review_notes: candidateDetailFallback.reviewNotes,
    next_actions: candidateDetailFallback.nextActions
  });

  return {
    id: response.id,
    name: response.name,
    role: response.role,
    phone: response.phone,
    email: response.email,
    city: response.city,
    skills: response.skills,
    projectSummary: response.project_summary,
    markdownPreview: response.markdown_preview,
    avatarUrl: apiUrl(response.avatar_url),
    parseMetrics: {
      firstPageCharacters: response.parse_metrics.first_page_characters,
      multimodalPages: response.parse_metrics.multimodal_pages,
      confidence: response.parse_metrics.confidence
    },
    reviewNotes: response.review_notes,
    nextActions: response.next_actions
  };
}

export async function loadLatestResumeBatchAnalysis(): Promise<BatchAnalysis> {
  const response = await requestJson<{
    batch_id: string | null;
    output_dir?: string;
    analysis_markdown: string;
  }>("/admin/resume-batches/latest/analysis", undefined, {
    batch_id: null,
    analysis_markdown:
      "# 简历批量共性分析\n\n暂无真实批量解析结果。上传或运行批处理后，这里会展示技能矩阵、共性主题和复核提示。\n"
  });

  return {
    batchId: response.batch_id,
    outputDir: response.output_dir,
    analysisMarkdown: response.analysis_markdown
  };
}

export async function loadPaperDraft(paperId: string): Promise<PaperDraft> {
  const response = await requestJson<{
    paper_id: string;
    title: string;
    mix: Record<string, number>;
    questions: PaperDraft["questions"];
  }>(`/admin/papers/${paperId}`, undefined, {
    paper_id: paperDraftFallback.paperId,
    title: paperDraftFallback.title,
    mix: paperDraftFallback.mix,
    questions: paperDraftFallback.questions
  });

  return {
    paperId: response.paper_id,
    title: response.title,
    mix: response.mix,
    questions: response.questions
  };
}

export async function loadExamShell(token: string): Promise<ExamShellPayload> {
  const response = await requestJson<{
    token: string;
    paper_title: string;
    duration_minutes: number;
    heartbeat_interval_ms: number;
    autosave_interval_ms: number;
    risk_events: string[];
    questions: Array<{
      id: string;
      kind: ExamQuestion["kind"];
      short_label: string;
      type_label: string;
      title: string;
      description: string;
      score: number;
      fields?: string[];
      options?: string[];
      language?: string;
      supported_languages?: string[];
      starter_code?: string;
    }>;
  }>(`/public/exams/${token}`, undefined, {
    token,
    paper_title: examShellFallback.paperTitle,
    duration_minutes: examShellFallback.durationMinutes,
    heartbeat_interval_ms: examShellFallback.heartbeatIntervalMs,
    autosave_interval_ms: examShellFallback.autosaveIntervalMs,
    risk_events: examShellFallback.riskEvents,
    questions: examShellFallback.questions.map((question) => ({
      id: question.id,
      kind: question.kind,
      short_label: question.shortLabel,
      type_label: question.typeLabel,
      title: question.title,
      description: question.description,
      score: question.score,
      fields: question.fields,
      options: question.options,
      language: question.language,
      supported_languages: question.supportedLanguages,
      starter_code: question.starterCode
    }))
  });

  return {
    token: response.token,
    paperTitle: response.paper_title,
    durationMinutes: response.duration_minutes,
    heartbeatIntervalMs: response.heartbeat_interval_ms,
    autosaveIntervalMs: response.autosave_interval_ms,
    riskEvents: response.risk_events,
    questions: response.questions.map((question) => ({
      id: question.id,
      kind: question.kind,
      shortLabel: question.short_label,
      typeLabel: question.type_label,
      title: question.title,
      description: question.description,
      score: question.score,
      fields: question.fields,
      options: question.options,
      language: question.language,
      supportedLanguages: question.supported_languages,
      starterCode: question.starter_code
    }))
  };
}

export async function saveDraftAnswer(
  token: string,
  questionId: string,
  draftAnswer: Record<string, unknown>
): Promise<void> {
  await requestJson(
    `/public/exams/${token}/answers/${questionId}`,
    {
      method: "PUT",
      body: JSON.stringify({ draft_answer: draftAnswer })
    },
    { status: "saved" }
  );
}

export async function sendHeartbeat(token: string): Promise<void> {
  await requestJson(
    `/public/exams/${token}/heartbeat`,
    {
      method: "POST"
    },
    { status: "accepted" }
  );
}

export async function sendRiskEvent(
  token: string,
  eventType: string,
  payload: Record<string, unknown> = {}
): Promise<void> {
  await requestJson(
    `/public/exams/${token}/risk-events`,
    {
      method: "POST",
      body: JSON.stringify({ event_type: eventType, payload })
    },
    { status: "accepted" }
  );
}

export async function runCodingQuestion(
  token: string,
  payload: { language: string; sourceCode: string; stdin: string }
): Promise<CodingRunResult> {
  return requestJson<CodingRunResult>(`/public/exams/${token}/coding/run`, {
    method: "POST",
    body: JSON.stringify({
      language: payload.language,
      source_code: payload.sourceCode,
      stdin: payload.stdin
    })
  });
}

export async function submitCodingQuestion(
  token: string,
  payload: { questionId: string; language: string; sourceCode: string }
): Promise<CodingSubmitResult> {
  return requestJson<CodingSubmitResult>(`/public/exams/${token}/coding/submit`, {
    method: "POST",
    body: JSON.stringify({
      question_id: payload.questionId,
      language: payload.language,
      source_code: payload.sourceCode
    })
  });
}
