const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";
const ADMIN_SESSION_STORAGE_KEY = "pre-screen:admin-session";

export type AdminSession = {
  sessionToken: string;
  userName: string;
  role: string;
};

export type DashboardCandidate = {
  candidateId: string;
  name: string;
  role: string;
  status: string;
  resumeUploadedAt?: string;
  profileCompletedAt?: string;
  target: string;
};

export type DashboardResult = {
  resultId: string;
  candidateId: string;
  candidateName: string;
  role: string;
  status: string;
  submittedAt: string;
  totalScore: number;
  target: string;
};

export type AdminDashboard = {
  metrics: {
    screeningCandidateCount: number;
    pendingPublishCount: number;
    examInProgressCount: number;
    submittedCount: number;
    screeningCompletedCount: number;
  };
  screeningCandidates: DashboardCandidate[];
  pendingPublishCandidates: DashboardCandidate[];
  submittedResults: DashboardResult[];
};

export type ScreeningTaskSummary = {
  id: string;
  title: string;
  role: string;
  status: string;
  candidateCount: number;
  uploadCount: number;
  createdAt: string;
};

export type ProcessingStepStatus = {
  label: string;
  status: string;
};

export type ProcessingStatus = {
  stage: string;
  status: string;
  progress: number;
  message: string;
  errorMessage?: string | null;
  steps: Record<string, ProcessingStepStatus>;
};

export type ParseJobSummary = {
  id: string;
  fileName: string;
  status: string;
  progress: number;
  candidateId?: string | null;
  createdAt: string;
  updatedAt: string;
  processing?: ProcessingStatus | null;
};

export type CandidateCard = {
  id: string;
  taskId: string;
  name: string;
  role: string;
  city: string;
  status: string;
  quality: string;
  summary: string;
  skills: string[];
  paperId?: string | null;
  resultId?: string | null;
  processing?: ProcessingStatus | null;
};

export type CandidateProject = {
  projectId: string;
  name: string;
  role: string;
  summary: string;
  techStack: string[];
  responsibilities: string[];
  achievements: string[];
  metrics: string[];
  sourcePages: number[];
  confidence: string;
};

export type CandidateAnalysis = {
  focusTopics: string[];
  strengths: string[];
  risks: string[];
  recommendedLanguages: string[];
  missingFields: string[];
};

export type CandidateDetail = {
  id: string;
  taskId: string;
  name: string;
  role: string;
  email: string;
  city: string;
  phone: string;
  status: string;
  quality: string;
  skills: string[];
  hobbies: string[];
  heightCm?: number | null;
  weightKg?: number | null;
  availableInDays?: number | null;
  projectSummary: string;
  projects: CandidateProject[];
  analysis: CandidateAnalysis;
  processing?: ProcessingStatus | null;
  reviewNotes: string[];
  parseMetrics: {
    firstPageCharacters: number;
    multimodalPages: number;
    confidence: string;
  };
  paperId?: string | null;
  invitationToken?: string | null;
  resultId?: string | null;
};

export type CandidateEditPayload = {
  name: string;
  role: string;
  email: string;
  city: string;
  phone: string;
  skills: string[];
  hobbies: string[];
  heightCm?: number | null;
  weightKg?: number | null;
  availableInDays?: number | null;
  projectSummary: string;
  reviewNotes: string[];
};

export type PaperQuestion = {
  id: string;
  kind: "base_info" | "objective" | "subjective" | "coding";
  title: string;
  description: string;
  score: number;
  fields?: string[];
  options?: string[];
  answerKey?: string | string[];
  rubricText?: string;
  language?: string;
  supportedLanguages?: string[];
  starterCode?: string;
};

export type PaperDraft = {
  paperId: string;
  candidateId: string;
  title: string;
  durationMinutes: number;
  status: "draft" | "published";
  introduction: string;
  mix: Record<string, number>;
  questions: PaperQuestion[];
  generationSummary?: {
    matchedProjects: string[];
    focusTopics: string[];
    generationNotes: string[];
    codingTheme?: string;
    codingLanguage?: string;
  };
  invitation?: {
    token: string;
    verifyCode: string;
    startUrl: string;
    status: string;
  } | null;
};

export type ResultSummary = {
  resultId: string;
  candidateId: string;
  candidateName: string;
  role: string;
  submittedAt: string;
  totalScore: number;
  status: string;
};

export type ResultDetail = {
  resultId: string;
  candidate: {
    id: string;
    name: string;
    role: string;
  };
  invitation: {
    token: string;
    submittedAt: string;
  };
  summary: {
    objectiveScore: number;
    subjectiveScore: number;
    codingScore: number;
    totalScore: number;
    riskSummary: Record<string, unknown>;
  };
  answers: Array<{
    questionId: string;
    title: string;
    kind: string;
    answer: unknown;
    score: number;
    comment?: string;
  }>;
  coding?: {
    language: string;
    sourceCode: string;
    summary: {
      passedCount: number;
      failedCount: number;
      totalScore: number;
      maxScore: number;
    };
    results: Array<{
      stdin: string;
      expectedStdout: string;
      actualStdout: string;
      passed: boolean;
      score: number;
    }>;
  } | null;
};

function mapProcessingStatus(input?: {
  stage?: string;
  status?: string;
  progress?: number;
  message?: string;
  error_message?: string | null;
  steps?: Record<string, { label?: string; status?: string }>;
} | null): ProcessingStatus | null {
  if (!input) {
    return null;
  }

  const steps = Object.fromEntries(
    Object.entries(input.steps ?? {}).map(([key, item]) => [
      key,
      {
        label: item.label ?? key,
        status: item.status ?? "pending"
      }
    ])
  );

  return {
    stage: input.stage ?? "unknown",
    status: input.status ?? "unknown",
    progress: input.progress ?? 0,
    message: input.message ?? "",
    errorMessage: input.error_message,
    steps
  };
}

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

export type PublicExamPayload = {
  token: string;
  state: "not_started" | "in_progress" | "submitted";
  candidateName: string;
  paperTitle: string;
  durationMinutes: number;
  heartbeatIntervalMs: number;
  autosaveIntervalMs: number;
  riskEvents: string[];
  instructions: string[];
  questions: ExamQuestion[];
  startedAt?: string | null;
  expiresAt?: string | null;
  lastHeartbeatAt?: string | null;
  answers?: Record<string, Record<string, unknown>>;
  submissionSummary?: {
    submittedAt: string;
    totalScore: number;
    objectiveScore: number;
    subjectiveScore: number;
    codingScore: number;
  } | null;
};

export type CodingRunResult = {
  mode: "run";
  stdout: string | null;
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

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

async function requestJson<T>(path: string, init?: RequestInit, fallback?: T): Promise<T> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: {
        ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
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

const fallbackSession: AdminSession = {
  sessionToken: "demo-admin-token",
  userName: "Ray HR",
  role: "HR"
};

export async function loginAdmin(username: string, password: string): Promise<AdminSession> {
  const response = await requestJson<{
    token?: string;
    session_token?: string;
    user_name?: string;
    role?: string;
    user?: {
      username?: string;
      display_name?: string;
      role?: string;
    };
  }>(
    "/admin/session/login",
    {
      method: "POST",
      body: JSON.stringify({ username, password })
    },
    {
      session_token: fallbackSession.sessionToken,
      user_name: fallbackSession.userName,
      role: fallbackSession.role
    }
  );

  return {
    sessionToken: response.session_token ?? response.token ?? fallbackSession.sessionToken,
    userName: response.user_name ?? response.user?.display_name ?? response.user?.username ?? fallbackSession.userName,
    role: response.role ?? response.user?.role ?? fallbackSession.role
  };
}

export async function fetchAdminSession(): Promise<AdminSession> {
  let headers: HeadersInit | undefined;
  if (typeof window !== "undefined") {
    const raw = window.localStorage.getItem(ADMIN_SESSION_STORAGE_KEY);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as AdminSession;
        if (parsed.sessionToken) {
          headers = { Authorization: `Bearer ${parsed.sessionToken}` };
        }
      } catch {
        headers = undefined;
      }
    }
  }
  const response = await requestJson<{
    token?: string;
    session_token?: string;
    username?: string;
    user_name?: string;
    display_name?: string;
    role?: string;
  }>("/admin/session/me", { headers }, {
    session_token: fallbackSession.sessionToken,
    user_name: fallbackSession.userName,
    role: fallbackSession.role
  });

  return {
    sessionToken: response.session_token ?? response.token ?? fallbackSession.sessionToken,
    userName: response.user_name ?? response.display_name ?? response.username ?? fallbackSession.userName,
    role: response.role ?? fallbackSession.role
  };
}

export async function loadDashboard(): Promise<AdminDashboard> {
  const response = await requestJson<{
    metrics: {
      screening_candidate_count: number;
      pending_publish_count: number;
      exam_in_progress_count: number;
      submitted_count: number;
      screening_completed_count: number;
    };
    screening_candidates: Array<{
      candidate_id: string;
      name: string;
      role: string;
      status: string;
      resume_uploaded_at?: string;
      target: string;
    }>;
    pending_publish_candidates: Array<{
      candidate_id: string;
      name: string;
      role: string;
      status: string;
      profile_completed_at?: string;
      target: string;
    }>;
    submitted_results: Array<{
      result_id: string;
      candidate_id: string;
      candidate_name: string;
      role: string;
      status: string;
      submitted_at: string;
      total_score: number;
      target: string;
    }>;
  }>("/admin/dashboard");

  return {
    metrics: {
      screeningCandidateCount: response.metrics.screening_candidate_count,
      pendingPublishCount: response.metrics.pending_publish_count,
      examInProgressCount: response.metrics.exam_in_progress_count,
      submittedCount: response.metrics.submitted_count,
      screeningCompletedCount: response.metrics.screening_completed_count
    },
    screeningCandidates: response.screening_candidates.map((item) => ({
      candidateId: item.candidate_id,
      name: item.name,
      role: item.role,
      status: item.status,
      resumeUploadedAt: item.resume_uploaded_at,
      target: item.target
    })),
    pendingPublishCandidates: response.pending_publish_candidates.map((item) => ({
      candidateId: item.candidate_id,
      name: item.name,
      role: item.role,
      status: item.status,
      profileCompletedAt: item.profile_completed_at,
      target: item.target
    })),
    submittedResults: response.submitted_results.map((item) => ({
      resultId: item.result_id,
      candidateId: item.candidate_id,
      candidateName: item.candidate_name,
      role: item.role,
      status: item.status,
      submittedAt: item.submitted_at,
      totalScore: item.total_score,
      target: item.target
    }))
  };
}

export async function loadTasks(): Promise<ScreeningTaskSummary[]> {
  const response = await requestJson<{ items: Array<{
    id?: string;
    task_id?: string;
    title: string;
    role?: string;
    department?: string;
    status: string;
    candidate_count: number;
    upload_count?: number;
    created_at: string;
  }> }>("/admin/tasks", undefined, { items: [] });

  return response.items.map((item) => ({
    id: item.id ?? item.task_id ?? "",
    title: item.title,
    role: item.role ?? item.department ?? item.title,
    status: item.status,
    candidateCount: item.candidate_count,
    uploadCount: item.upload_count ?? 0,
    createdAt: item.created_at
  }));
}

export async function createTask(payload: {
  title: string;
  role: string;
  jdText: string;
  templateName: string;
}): Promise<ScreeningTaskSummary> {
  const response = await requestJson<{
    id?: string;
    task_id?: string;
    title: string;
    role?: string;
    department?: string;
    status: string;
    candidate_count: number;
    upload_count?: number;
    created_at: string;
  }>("/admin/tasks", {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      department: payload.role,
      city: "深圳",
      jd_text: payload.jdText,
      tags: payload.role.split(/[ /,]+/).filter(Boolean),
      template_name: payload.templateName,
      template_config: {
        base_info_count: 1,
        objective_count: 2,
        subjective_count: 1,
        coding_count: 1
      },
      duration_minutes: 90
    })
  });

  return {
    id: response.id ?? response.task_id ?? "",
    title: response.title,
    role: response.role ?? response.department ?? payload.role,
    status: response.status,
    candidateCount: response.candidate_count,
    uploadCount: response.upload_count ?? 0,
    createdAt: response.created_at
  };
}

export async function loadTaskDetail(taskId: string): Promise<{
  id: string;
  title: string;
  role: string;
  status: string;
  jdText: string;
  uploads: ParseJobSummary[];
  candidates: CandidateCard[];
}> {
  const response = await requestJson<{
    id?: string;
    task_id?: string;
    title: string;
    role?: string;
    department?: string;
    status: string;
    jd_text: string;
    uploads: Array<{
      id?: string;
      upload_id?: string;
      file_name?: string;
      filename?: string;
      status: string;
      progress: number;
      candidate_id?: string | null;
      created_at: string;
      updated_at: string;
      processing?: {
        stage?: string;
        status?: string;
        progress?: number;
        message?: string;
        error_message?: string | null;
        steps?: Record<string, { label?: string; status?: string }>;
      } | null;
    }>;
    candidates: Array<{
      id: string;
      task_id: string;
      name: string;
      role: string;
      city: string;
      status: string;
      quality: string;
      summary: string;
      skills: string[];
      paper_id?: string | null;
      result_id?: string | null;
      processing?: {
        stage?: string;
        status?: string;
        progress?: number;
        message?: string;
        error_message?: string | null;
        steps?: Record<string, { label?: string; status?: string }>;
      } | null;
    }>;
  }>(`/admin/tasks/${taskId}`);

  return {
    id: response.id ?? response.task_id ?? taskId,
    title: response.title,
    role: response.role ?? response.department ?? response.title,
    status: response.status,
    jdText: response.jd_text,
    uploads: (response.uploads ?? []).map((item) => ({
      id: item.id ?? item.upload_id ?? "",
      fileName: item.file_name ?? item.filename ?? "",
      status: item.status,
      progress: item.progress,
      candidateId: item.candidate_id,
      createdAt: item.created_at,
      updatedAt: item.updated_at,
      processing: mapProcessingStatus(item.processing)
    })),
    candidates: response.candidates.map(mapCandidateCard)
  };
}

export async function uploadTaskResumes(taskId: string, files: File[]): Promise<ParseJobSummary[]> {
  const form = new FormData();
  files.forEach((file) => {
    form.append("files", file, file.name);
  });

  const response = await requestJson<{ items: Array<{
    id?: string;
    upload_id?: string;
    file_name?: string;
    filename?: string;
    status: string;
    progress: number;
    candidate_id?: string | null;
    created_at: string;
    updated_at: string;
    processing?: {
      stage?: string;
      status?: string;
      progress?: number;
      message?: string;
      error_message?: string | null;
      steps?: Record<string, { label?: string; status?: string }>;
    } | null;
  }> }>(`/admin/tasks/${taskId}/uploads`, {
    method: "POST",
    body: form
  });

  return response.items.map((item) => ({
    id: item.id ?? item.upload_id ?? "",
    fileName: item.file_name ?? item.filename ?? "",
    status: item.status,
    progress: item.progress,
    candidateId: item.candidate_id,
    createdAt: item.created_at,
    updatedAt: item.updated_at,
    processing: mapProcessingStatus(item.processing)
  }));
}

function mapCandidateCard(item: {
  id: string;
  task_id: string;
  name: string;
  role: string;
  city: string;
  status: string;
  quality: string;
  summary: string;
  skills: string[];
  paper_id?: string | null;
  result_id?: string | null;
  processing?: {
    stage?: string;
    status?: string;
    progress?: number;
    message?: string;
    error_message?: string | null;
    steps?: Record<string, { label?: string; status?: string }>;
  } | null;
}): CandidateCard {
  return {
    id: item.id,
    taskId: item.task_id,
    name: item.name,
    role: item.role,
    city: item.city,
    status: item.status,
    quality: item.quality,
    summary: item.summary,
    skills: item.skills,
    paperId: item.paper_id,
    resultId: item.result_id,
    processing: mapProcessingStatus(item.processing)
  };
}

export async function loadCandidates(taskId?: string): Promise<CandidateCard[]> {
  const query = taskId ? `?task_id=${encodeURIComponent(taskId)}` : "";
  const response = await requestJson<{ items: Array<{
    id: string;
    task_id: string;
    name: string;
    role: string;
    city: string;
    status: string;
    quality: string;
    summary: string;
    skills: string[];
    paper_id?: string | null;
    result_id?: string | null;
    processing?: {
      stage?: string;
      status?: string;
      progress?: number;
      message?: string;
      error_message?: string | null;
      steps?: Record<string, { label?: string; status?: string }>;
    } | null;
  }> }>(`/admin/candidates${query}`, undefined, { items: [] });

  return response.items.map(mapCandidateCard);
}

export async function loadCandidateDetail(candidateId: string): Promise<CandidateDetail> {
  const response = await requestJson<{
    id: string;
    task_id: string;
    name: string;
    role: string;
    email: string;
    city: string;
    phone: string;
    status: string;
    quality: string;
    skills: string[];
    hobbies: string[];
    height_cm?: number | null;
    weight_kg?: number | null;
    available_in_days?: number | null;
    project_summary: string;
    projects?: Array<{
      project_id: string;
      name: string;
      role: string;
      summary: string;
      tech_stack?: string[];
      responsibilities?: string[];
      achievements?: string[];
      metrics?: string[];
      source_pages?: number[];
      confidence?: string;
    }>;
    analysis?: {
      focus_topics?: string[];
      strengths?: string[];
      risks?: string[];
      recommended_languages?: string[];
      missing_fields?: string[];
    };
    processing?: {
      stage?: string;
      status?: string;
      progress?: number;
      message?: string;
      error_message?: string | null;
      steps?: Record<string, { label?: string; status?: string }>;
    } | null;
    review_notes: string[];
    parse_metrics: {
      first_page_characters: number;
      multimodal_pages: number;
      confidence: string;
    };
    next_actions?: Array<{ label?: string; target?: string }>;
    paper_id?: string | null;
    invitation_token?: string | null;
    result_id?: string | null;
  }>(`/admin/candidates/${candidateId}`);

  const derivedPaperId =
    response.paper_id ??
    response.next_actions?.find((item) => item.target?.includes("/admin/papers/"))?.target?.match(/\/admin\/papers\/([^/?#]+)/)?.[1] ??
    null;

  return {
    id: response.id,
    taskId: response.task_id,
    name: response.name,
    role: response.role,
    email: response.email,
    city: response.city,
    phone: response.phone ?? "",
    status: response.status ?? "待审核",
    quality: response.quality ?? response.parse_metrics.confidence,
    skills: response.skills,
    hobbies: response.hobbies ?? [],
    heightCm: response.height_cm,
    weightKg: response.weight_kg,
    availableInDays: response.available_in_days,
    projectSummary: response.project_summary,
    projects: (response.projects ?? []).map((project) => ({
      projectId: project.project_id,
      name: project.name,
      role: project.role ?? "",
      summary: project.summary ?? "",
      techStack: project.tech_stack ?? [],
      responsibilities: project.responsibilities ?? [],
      achievements: project.achievements ?? [],
      metrics: project.metrics ?? [],
      sourcePages: project.source_pages ?? [],
      confidence: project.confidence ?? "medium"
    })),
    analysis: {
      focusTopics: response.analysis?.focus_topics ?? [],
      strengths: response.analysis?.strengths ?? [],
      risks: response.analysis?.risks ?? [],
      recommendedLanguages: response.analysis?.recommended_languages ?? [],
      missingFields: response.analysis?.missing_fields ?? []
    },
    processing: mapProcessingStatus(response.processing),
    reviewNotes: response.review_notes,
    parseMetrics: {
      firstPageCharacters: response.parse_metrics.first_page_characters,
      multimodalPages: response.parse_metrics.multimodal_pages,
      confidence: response.parse_metrics.confidence
    },
    paperId: derivedPaperId,
    invitationToken: response.invitation_token,
    resultId: response.result_id
  };
}

export async function updateCandidateDetail(
  candidateId: string,
  payload: CandidateEditPayload
): Promise<CandidateDetail> {
  const response = await requestJson(`/admin/candidates/${candidateId}`, {
    method: "PUT",
    body: JSON.stringify({
      name: payload.name,
      role: payload.role,
      email: payload.email,
      city: payload.city,
      phone: payload.phone,
      skills: payload.skills,
      hobbies: payload.hobbies,
      height_cm: payload.heightCm,
      weight_kg: payload.weightKg,
      available_in_days: payload.availableInDays,
      project_summary: payload.projectSummary,
      review_notes: payload.reviewNotes
    })
  });

  return loadCandidateDetail(candidateId);
}

function mapPaperQuestion(item: {
  id: string;
  kind: PaperQuestion["kind"];
  title: string;
  description: string;
  score: number;
  fields?: string[];
  options?: string[];
  answer_key?: string | string[];
  rubric_text?: string;
  language?: string;
  supported_languages?: string[];
  starter_code?: string;
}): PaperQuestion {
  return {
    id: item.id,
    kind: item.kind,
    title: item.title,
    description: item.description,
    score: item.score,
    fields: item.fields,
    options: item.options,
    answerKey: item.answer_key,
    rubricText: item.rubric_text,
    language: item.language,
    supportedLanguages: item.supported_languages,
    starterCode: item.starter_code
  };
}

export async function generatePaper(candidateId: string): Promise<PaperDraft> {
  const response = await requestJson<{ paper_id: string }>(`/admin/candidates/${candidateId}/papers/generate`, {
    method: "POST"
  });
  return loadPaperDraft(response.paper_id);
}

export async function loadPaperDraft(paperId: string): Promise<PaperDraft> {
  const response = await requestJson<{
    paper_id: string;
    candidate_id: string;
    title: string;
    duration_minutes: number;
    status: "draft" | "published";
    introduction?: string;
    mix: Record<string, number>;
    questions: Array<{
      id: string;
      kind: PaperQuestion["kind"];
      title: string;
      description: string;
      score: number;
      fields?: string[];
      options?: string[];
      answer_key?: string | string[];
      rubric_text?: string;
      language?: string;
      supported_languages?: string[];
      starter_code?: string;
    }>;
    invitation?: {
      token: string;
      verify_code: string;
      start_url: string;
      status: string;
    } | null;
    generation_summary?: {
      matched_projects?: string[];
      focus_topics?: string[];
      generation_notes?: string[];
      coding_theme?: string;
      coding_language?: string;
    };
  }>(`/admin/papers/${paperId}`);

  return {
    paperId: response.paper_id,
    candidateId: response.candidate_id,
    title: response.title,
    durationMinutes: response.duration_minutes,
    status: response.status,
    introduction: response.introduction ?? "请先完成基础信息，再依次完成客观题、主观题和代码题。",
    mix: response.mix,
    questions: response.questions.map(mapPaperQuestion),
    generationSummary: response.generation_summary
      ? {
          matchedProjects: response.generation_summary.matched_projects ?? [],
          focusTopics: response.generation_summary.focus_topics ?? [],
          generationNotes: response.generation_summary.generation_notes ?? [],
          codingTheme: response.generation_summary.coding_theme,
          codingLanguage: response.generation_summary.coding_language
        }
      : undefined,
    invitation: response.invitation
      ? {
          token: response.invitation.token,
          verifyCode: response.invitation.verify_code,
          startUrl: response.invitation.start_url,
          status: response.invitation.status
        }
      : null
  };
}

export async function savePaperDraft(
  paperId: string,
  payload: { title: string; durationMinutes: number; introduction: string; questions: PaperQuestion[] }
): Promise<PaperDraft> {
  await requestJson(`/admin/papers/${paperId}`, {
    method: "PUT",
    body: JSON.stringify({
      title: payload.title,
      duration_minutes: payload.durationMinutes,
      introduction: payload.introduction,
      questions: payload.questions.map((question) => ({
        id: question.id,
        kind: question.kind,
        title: question.title,
        description: question.description,
        score: question.score,
        fields: question.fields,
        options: question.options,
        answer_key: question.answerKey,
        rubric_text: question.rubricText,
        language: question.language,
        supported_languages: question.supportedLanguages,
        starter_code: question.starterCode
      }))
    })
  });

  return loadPaperDraft(paperId);
}

export async function publishPaper(paperId: string): Promise<PaperDraft["invitation"]> {
  const response = await requestJson<{
    token: string;
    verify_code?: string;
    verification_code?: string;
    start_url?: string;
    exam_url?: string;
    status?: string;
    access_state?: string;
  }>(`/admin/papers/${paperId}/publish`, {
    method: "POST"
  });

  return {
    token: response.token,
    verifyCode: response.verify_code ?? response.verification_code ?? "",
    startUrl: response.start_url ?? response.exam_url ?? "",
    status: response.status ?? response.access_state ?? "published"
  };
}

export async function loadResults(): Promise<ResultSummary[]> {
  const response = await requestJson<{ items: Array<{
    result_id: string;
    candidate_id: string;
    candidate_name: string;
    role?: string;
    paper_title?: string;
    submitted_at: string;
    total_score: number;
    status: string;
  }> }>("/admin/results", undefined, { items: [] });

  return response.items.map((item) => ({
    resultId: item.result_id,
    candidateId: item.candidate_id,
    candidateName: item.candidate_name,
    role: item.role ?? item.paper_title ?? "在线测评",
    submittedAt: item.submitted_at,
    totalScore: item.total_score,
    status: item.status
  }));
}

export async function loadResultDetail(resultId: string): Promise<ResultDetail> {
  const response = await requestJson<{
    result_id: string;
    candidate: {
      id: string;
      name: string;
      role: string;
      invitation_token?: string | null;
    };
    invitation?: { token: string; submitted_at: string };
    submitted_at?: string;
    summary: {
      objective_score: number;
      subjective_score: number;
      coding_score: number;
      total_score: number;
      risk_summary: Record<string, unknown>;
    };
    answers: Array<{
      question_id?: string;
      title: string;
      kind: string;
      answer?: unknown;
      draft_answer?: unknown;
      score: number;
      comment?: string;
      reasoning_summary?: string;
    }>;
    coding?: {
      language: string;
      source_code: string;
      summary: {
        passed_count: number;
        failed_count: number;
        total_score: number;
        max_score: number;
      };
      results: Array<{
        stdin: string;
        expected_stdout: string;
        actual_stdout: string;
        passed: boolean;
        score: number;
      }>;
    } | null;
  }>(`/admin/results/${resultId}`);

  return {
    resultId: response.result_id,
    candidate: response.candidate,
    invitation: {
      token: response.invitation?.token ?? response.candidate.invitation_token ?? "",
      submittedAt: response.invitation?.submitted_at ?? response.submitted_at ?? ""
    },
    summary: {
      objectiveScore: response.summary.objective_score,
      subjectiveScore: response.summary.subjective_score,
      codingScore: response.summary.coding_score,
      totalScore: response.summary.total_score,
      riskSummary: response.summary.risk_summary
    },
    answers: response.answers.map((item) => ({
      questionId: item.question_id ?? "",
      title: item.title,
      kind: item.kind,
      answer: item.answer ?? item.draft_answer,
      score: item.score,
      comment: item.comment ?? item.reasoning_summary
    })),
    coding: response.coding
      ? {
          language: response.coding.language,
          sourceCode: response.coding.source_code,
          summary: {
            passedCount: response.coding.summary.passed_count,
            failedCount: response.coding.summary.failed_count,
            totalScore: response.coding.summary.total_score,
            maxScore: response.coding.summary.max_score
          },
          results: response.coding.results.map((item) => ({
            stdin: item.stdin,
            expectedStdout: item.expected_stdout,
            actualStdout: item.actual_stdout,
            passed: item.passed,
            score: item.score
          }))
        }
      : null
  };
}

export async function loadPublicExam(token: string): Promise<PublicExamPayload> {
  const response = await requestJson<{
    token: string;
    state?: PublicExamPayload["state"];
    access_state?: PublicExamPayload["state"];
    candidate_name: string;
    paper_title: string;
    duration_minutes: number;
    heartbeat_interval_ms: number;
    autosave_interval_ms: number;
    risk_events: string[];
    instructions?: string[];
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
    started_at?: string | null;
    expires_at?: string | null;
    submitted_at?: string | null;
    last_heartbeat_at?: string | null;
    answers?: Record<string, Record<string, unknown>>;
    submission_summary?: {
      submitted_at: string;
      total_score: number;
      objective_score: number;
      subjective_score: number;
      coding_score: number;
    } | null;
  }>(`/public/exams/${token}`);

  return {
    token: response.token,
    state: response.state ?? response.access_state ?? "not_started",
    candidateName: response.candidate_name,
    paperTitle: response.paper_title,
    durationMinutes: response.duration_minutes,
    heartbeatIntervalMs: response.heartbeat_interval_ms,
    autosaveIntervalMs: response.autosave_interval_ms,
    riskEvents: response.risk_events,
    instructions:
      response.instructions ?? [
        "请输入验证码进入考试。",
        "系统会自动保存答案，并记录基础风控事件。",
        "交卷后 HR 将查看评分与作答详情。"
      ],
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
    })),
    startedAt: response.started_at,
    expiresAt: response.expires_at,
    lastHeartbeatAt: response.last_heartbeat_at,
    answers: response.answers ?? {},
    submissionSummary: response.submission_summary
      ? {
          submittedAt: response.submission_summary.submitted_at,
          totalScore: response.submission_summary.total_score,
          objectiveScore: response.submission_summary.objective_score,
          subjectiveScore: response.submission_summary.subjective_score,
          codingScore: response.submission_summary.coding_score
        }
      : response.submitted_at
        ? {
            submittedAt: response.submitted_at,
            totalScore: 0,
            objectiveScore: 0,
            subjectiveScore: 0,
            codingScore: 0
          }
        : null
  };
}

export async function startPublicExam(token: string, verificationCode: string): Promise<PublicExamPayload> {
  await requestJson(`/public/exams/${token}/start`, {
    method: "POST",
    body: JSON.stringify({ verification_code: verificationCode })
  });
  return loadPublicExam(token);
}

export async function saveDraftAnswer(
  token: string,
  questionId: string,
  draftAnswer: Record<string, unknown>
): Promise<void> {
  await requestJson(`/public/exams/${token}/answers/${questionId}`, {
    method: "PUT",
    body: JSON.stringify({ draft_answer: draftAnswer })
  });
}

export async function sendHeartbeat(token: string): Promise<void> {
  await requestJson(`/public/exams/${token}/heartbeat`, {
    method: "POST"
  });
}

export async function sendRiskEvent(
  token: string,
  eventType: string,
  payload: Record<string, unknown> = {}
): Promise<void> {
  await requestJson(`/public/exams/${token}/risk-events`, {
    method: "POST",
    body: JSON.stringify({ event_type: eventType, payload })
  });
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

export async function submitExam(token: string): Promise<PublicExamPayload> {
  await requestJson(`/public/exams/${token}/submit`, {
    method: "POST"
  });
  return loadPublicExam(token);
}
