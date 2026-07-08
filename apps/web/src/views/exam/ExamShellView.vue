<template>
  <div class="shell-page exam-page">
    <section v-if="loading" class="glass-card state-card">
      <h2 class="section-title">加载中</h2>
    </section>

    <section v-else-if="loadError" class="glass-card state-card">
      <h2 class="section-title">无法进入考试</h2>
      <p class="section-copy">{{ loadError }}</p>
      <button class="primary-btn state-btn" type="button" @click="loadExamState">重试</button>
    </section>

    <section v-else-if="exam?.state === 'not_started'" class="glass-card gate-card">
      <div class="gate-hero">
        <div>
          <div class="pill">开始</div>
          <h1 class="gate-title">{{ exam.paperTitle }}</h1>
        </div>

        <div class="gate-metric-grid">
          <article class="metric-tile">
            <div class="metric-value">{{ exam.durationMinutes }}</div>
            <div class="metric-label">时长（分钟）</div>
          </article>
          <article class="metric-tile">
            <div class="metric-value">{{ questions.length }}</div>
            <div class="metric-label">总题量</div>
          </article>
        </div>
      </div>

      <div class="gate-layout">
        <section class="gate-section">
          <h2 class="section-title">注意事项</h2>
          <ul class="instruction-list">
            <li v-for="instruction in exam.instructions" :key="instruction">{{ instruction }}</li>
            <li>答案会自动保存，切屏等行为会被记录。</li>
          </ul>
        </section>
      </div>

      <label class="gate-field">
        <span>验证码</span>
        <input v-model="verificationCode" class="soft-input" placeholder="请输入 HR 发给你的验证码" />
      </label>

      <div class="gate-feedback" :class="{ 'gate-feedback--active': starting }">
        <strong>{{ startFeedback.title }}</strong>
        <span>{{ startFeedback.copy }}</span>
      </div>

      <div v-if="entryError" class="error-banner">{{ entryError }}</div>

      <button class="primary-btn gate-btn" type="button" :disabled="starting" @click="startExamSession">
        {{ starting ? "正在进入考试..." : "开始答题" }}
      </button>
    </section>

    <section v-else-if="exam?.state === 'submitted'" class="glass-card submitted-card">
      <div class="pill">已交卷</div>
      <h1 class="gate-title">考试完成</h1>
      <p class="section-copy">
        系统已经记录你的答案{{ exam.submissionSummary?.submittedAt ? `，提交时间 ${formatDateTime(exam.submissionSummary.submittedAt)}` : "" }}。
      </p>

      <div class="metric-grid">
        <article class="metric-tile">
          <div class="metric-value">{{ exam.submissionSummary?.totalScore ?? 0 }}</div>
          <div class="metric-label">总分</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ exam.submissionSummary?.objectiveScore ?? 0 }}</div>
          <div class="metric-label">客观题</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ exam.submissionSummary?.subjectiveScore ?? 0 }}</div>
          <div class="metric-label">主观题</div>
        </article>
        <article class="metric-tile">
          <div class="metric-value">{{ exam.submissionSummary?.codingScore ?? 0 }}</div>
          <div class="metric-label">代码题</div>
        </article>
      </div>
    </section>

    <div v-else-if="exam" class="exam-layout">
      <aside class="glass-card exam-sidebar">
        <div class="sidebar-head-wrap">
          <div>
            <div class="pill">Candidate Session</div>
            <h1 class="sidebar-head">{{ exam.paperTitle }}</h1>
            <p class="section-copy">{{ exam.candidateName }} · 已进入作答状态</p>
          </div>
          <span class="status-badge" :class="connectionStatus === 'offline' ? 'status-badge--danger' : 'status-badge--success'">
            {{ connectionStatus === "offline" ? "离线中" : "在线" }}
          </span>
        </div>

        <section class="progress-card">
          <div class="progress-card__head">
            <strong>题目进度</strong>
            <span>{{ currentQuestionNumber }} / {{ questions.length }}</span>
          </div>
          <div class="progress-copy">已完成 {{ answeredCount }} 题，剩余 {{ unansweredQuestions.length }} 题未完成</div>
          <div class="progress-track">
            <span :style="{ width: `${progressPercent}%` }" />
          </div>
        </section>

        <div class="session-block">
          <div class="timer-value">{{ countdownLabel }}</div>
          <div class="metric-label">剩余时间</div>
          <div class="session-inline-meta">
            <span>总时长 {{ exam.durationMinutes }} 分钟</span>
            <span>{{ questions.length }} 题</span>
          </div>
        </div>

        <section class="status-card">
          <div class="status-card__head">
            <strong>自动保存状态</strong>
            <span class="status-badge" :class="autosaveBadgeClass">{{ autosaveStatusLabel }}</span>
          </div>
          <p class="status-copy">{{ autosaveStatusCopy }}</p>
          <div class="status-card__meta">
            <span>{{ heartbeatStatusLabel }}</span>
            <span v-if="lastAutosaveAt">最近保存 {{ lastAutosaveAt }}</span>
          </div>
        </section>

        <div class="alert-stack">
          <div v-if="restoreNotice" class="alert-banner alert-banner--info">
            <strong>已恢复草稿</strong>
            <span>{{ restoreNotice }}</span>
          </div>
          <div v-if="networkNotice" class="alert-banner" :class="connectionStatus === 'offline' ? 'alert-banner--danger' : 'alert-banner--success'">
            <strong>{{ connectionStatus === "offline" ? "网络已断开" : "网络已恢复" }}</strong>
            <span>{{ networkNotice }}</span>
          </div>
          <div v-if="recentRiskMessage" class="alert-banner alert-banner--warning">
            <strong>过程记录提醒</strong>
            <span>{{ recentRiskMessage }}</span>
          </div>
        </div>

        <div class="nav-stack exam-nav">
          <button
            v-for="question in questions"
            :key="question.id"
            class="nav-item nav-button"
            :class="[
              { 'nav-item--active': store.activeQuestionId === question.id },
              `nav-item--${questionCompletionState(question)}`
            ]"
            @click="store.setActiveQuestion(question.id)"
          >
            <div class="nav-copy">
              <span>{{ question.shortLabel }}</span>
              <small>{{ question.title }}</small>
            </div>
            <div class="nav-meta">
              <em>{{ questionCompletionLabel(question) }}</em>
              <strong>{{ question.score }} 分</strong>
            </div>
          </button>
        </div>

        <div class="session-meta">
          <div>最后心跳：{{ store.lastHeartbeatAt || "等待首次保活中" }}</div>
          <div>本地已记录：{{ savedDraftCount }} 题</div>
          <div>风控记录：{{ store.riskEvents.length }} 条</div>
        </div>

        <button class="primary-btn submit-btn" type="button" :disabled="submittingExam" @click="openSubmitConfirm">
          {{ submittingExam ? "正在交卷..." : "提交试卷" }}
        </button>
      </aside>

      <main class="exam-main">
        <section class="glass-card intro-card">
          <div class="intro-head">
            <div>
              <div class="pill">Exam Flow</div>
              <h2 class="section-title">{{ activeQuestion?.title ?? "准备题目中..." }}</h2>
            </div>
            <div class="intro-badges">
              <span class="status-badge status-badge--neutral">{{ activeQuestion?.typeLabel ?? "题目" }}</span>
              <span
                class="status-badge"
                :class="activeQuestion ? completionBadgeClass(activeQuestion) : 'status-badge--neutral'"
              >
                {{ activeQuestion ? questionCompletionLabel(activeQuestion) : "准备中" }}
              </span>
            </div>
          </div>
          <p class="section-copy">{{ activeQuestion?.description ?? "系统正在准备题目。" }}</p>

          <div class="intro-meta">
            <span>当前进度 {{ currentQuestionNumber }} / {{ questions.length }}</span>
            <span v-if="activeQuestion">本题 {{ activeQuestion.score }} 分</span>
            <span>{{ autosaveShortCopy }}</span>
          </div>
        </section>

        <section v-if="restoreNotice || networkNotice || recentRiskMessage" class="exam-notice-grid">
          <article v-if="restoreNotice" class="notice-card">
            <strong>恢复提示</strong>
            <p>{{ restoreNotice }}</p>
          </article>
          <article v-if="networkNotice" class="notice-card" :class="connectionStatus === 'offline' ? 'notice-card--danger' : 'notice-card--success'">
            <strong>{{ connectionStatus === "offline" ? "离线提示" : "恢复提示" }}</strong>
            <p>{{ networkNotice }}</p>
          </article>
          <article v-if="recentRiskMessage" class="notice-card notice-card--warning">
            <strong>过程核验</strong>
            <p>{{ recentRiskMessage }}</p>
          </article>
        </section>

        <ExamQuestionPanel
          v-if="activeQuestion && activeQuestion.kind !== 'coding'"
          :question="{
            id: activeQuestion.id,
            title: activeQuestion.title,
            description: activeQuestion.description,
            score: activeQuestion.score,
            typeLabel: activeQuestion.typeLabel,
            mode: activeQuestion.kind as 'base_info' | 'objective' | 'subjective',
            fields: activeQuestion.fields,
            options: activeQuestion.options
          }"
          :model-value="store.answers[activeQuestion.id]"
          :progress-label="`第 ${currentQuestionNumber} / ${questions.length} 题`"
          :completion-label="questionCompletionLabel(activeQuestion)"
          :autosave-label="autosaveStatusLabel"
          @update:model-value="store.upsertDraftAnswer(activeQuestion.id, $event)"
        />

        <CodeQuestionPanel
          v-else-if="activeQuestion"
          :title="activeQuestion.title"
          :description="activeQuestion.description"
          :score="activeQuestion.score"
          :language="questionLanguage(activeQuestion)"
          :supported-languages="activeQuestion.supportedLanguages ?? [questionLanguage(activeQuestion)]"
          :code="codeValue(activeQuestion)"
          :run-input="runInput"
          :busy-mode="busyMode"
          :progress-label="`第 ${currentQuestionNumber} / ${questions.length} 题`"
          :autosave-label="autosaveStatusLabel"
          :run-feedback="activeQuestion.id === runFeedback?.questionId ? runFeedback : undefined"
          :submit-feedback="activeQuestion.id === submitFeedback?.questionId ? submitFeedback : undefined"
          @update:code="updateCodeAnswer(activeQuestion.id, $event)"
          @update:language="updateCodeLanguage(activeQuestion.id, $event)"
          @update:run-input="runInput = $event"
          @run="runActiveCode(activeQuestion)"
          @submit="submitActiveCode(activeQuestion)"
        />
      </main>
    </div>

    <section v-else class="glass-card state-card">
      <div class="pill">Candidate Session</div>
      <h2 class="section-title">考试信息不存在</h2>
      <p class="section-copy">请确认链接是否有效，或联系 HR 重新发送考试入口。</p>
    </section>

    <div v-if="showSubmitConfirm" class="modal-backdrop" @click.self="closeSubmitConfirm">
      <section class="glass-card submit-modal">
        <div class="pill">Submit Confirmation</div>
        <h2 class="section-title">确认现在交卷吗？</h2>
        <p class="section-copy">交卷后将无法继续修改答案。系统会按当前已保存内容提交整份试卷。</p>

        <div class="confirm-grid">
          <article class="metric-tile">
            <div class="metric-value">{{ answeredCount }}</div>
            <div class="metric-label">已完成题目</div>
          </article>
          <article class="metric-tile">
            <div class="metric-value">{{ unansweredQuestions.length }}</div>
            <div class="metric-label">未完成题目</div>
          </article>
          <article class="metric-tile">
            <div class="metric-value">{{ countdownLabel }}</div>
            <div class="metric-label">当前剩余时间</div>
          </article>
        </div>

        <div v-if="unansweredQuestions.length" class="confirm-warning">
          <strong>以下题目仍未完成：</strong>
          <span>{{ unansweredQuestionLabels }}</span>
        </div>

        <div v-if="connectionStatus === 'offline'" class="alert-banner alert-banner--danger confirm-alert">
          <strong>当前网络离线</strong>
          <span>建议先恢复网络，确认自动保存状态正常后再交卷。</span>
        </div>

        <div v-if="submitError" class="error-banner">{{ submitError }}</div>

        <div class="modal-actions">
          <button class="secondary-btn" type="button" @click="closeSubmitConfirm">再检查一下</button>
          <button class="primary-btn" type="button" :disabled="submittingExam" @click="submitCurrentExam">
            {{ submittingExam ? "正在交卷..." : "确认交卷" }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { useAutosave } from "../../composables/useAutosave";
import { useHeartbeat } from "../../composables/useHeartbeat";
import {
  loadPublicExam,
  runCodingQuestion,
  saveDraftAnswer,
  sendHeartbeat,
  sendRiskEvent,
  startPublicExam,
  submitCodingQuestion,
  submitExam,
  type CodingRunResult,
  type CodingSubmitResult,
  type ExamQuestion,
  type PublicExamPayload
} from "../../lib/gateway";
import { useExamSessionStore } from "../../stores/examSession";
import CodeQuestionPanel from "./CodeQuestionPanel.vue";
import ExamQuestionPanel from "./ExamQuestionPanel.vue";

type FeedbackState = "idle" | "running" | "success" | "error";

type RunFeedback = {
  questionId: string;
  state: FeedbackState;
  summary: string;
  detail?: string;
  updatedAt?: string;
};

type SubmitFeedback = {
  questionId: string;
  state: FeedbackState;
  summary: string;
  detail?: string;
  updatedAt?: string;
  passedCount?: number;
  failedCount?: number;
  totalScore?: number;
  maxScore?: number;
  cases?: Array<{
    index: number;
    passed: boolean;
    score: number;
    stdin: string;
    expected: string;
    actual: string;
    status: string;
  }>;
};

const route = useRoute();
const store = useExamSessionStore();

const exam = ref<PublicExamPayload | null>(null);
const loading = ref(true);
const loadError = ref("");
const starting = ref(false);
const submittingExam = ref(false);
const verificationCode = ref("");
const entryError = ref("");
const submitError = ref("");
const showSubmitConfirm = ref(false);
const nowMs = ref(Date.now());
const autosaveState = ref<"idle" | "pending" | "saving" | "saved" | "error">("idle");
const autosaveMessage = ref("系统会在你作答时自动保存答案。");
const lastAutosaveAt = ref("");
const restoreNotice = ref("");
const networkNotice = ref("");
const connectionStatus = ref<"online" | "offline">(
  typeof navigator !== "undefined" && !navigator.onLine ? "offline" : "online"
);
const storageKey = computed(() => `pre-screen:drafts:${String(route.params.token ?? "")}`);
const runInput = ref("[1,1,2,3,2]");
const busyMode = ref<"run" | "submit" | null>(null);
const runFeedback = ref<RunFeedback | null>(null);
const submitFeedback = ref<SubmitFeedback | null>(null);

let clockTimer: number | undefined;

const questions = computed(() => exam.value?.questions ?? []);
const activeQuestion = computed(
  () => questions.value.find((question) => question.id === store.activeQuestionId) ?? questions.value[0] ?? null
);
const savedDraftCount = computed(() => Object.keys(store.answers).length);
const answeredCount = computed(() => questions.value.filter((question) => questionCompletionState(question) === "done").length);
const unansweredQuestions = computed(() => questions.value.filter((question) => questionCompletionState(question) !== "done"));
const currentQuestionNumber = computed(() => {
  const currentIndex = questions.value.findIndex((question) => question.id === store.activeQuestionId);
  return currentIndex >= 0 ? currentIndex + 1 : questions.value.length ? 1 : 0;
});
const progressPercent = computed(() => {
  if (!questions.value.length) {
    return 0;
  }
  return Math.round((answeredCount.value / questions.value.length) * 100);
});
const countdownLabel = computed(() => {
  if (!store.expiresAt) {
    return "00:00";
  }
  const diff = new Date(store.expiresAt).getTime() - nowMs.value;
  const totalSeconds = Math.max(0, Math.floor(diff / 1000));
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
});
const startFeedback = computed(() => {
  if (starting.value) {
    return {
      title: "正在验证验证码并创建考试会话",
      copy: "系统会同步题目、恢复草稿，并启动自动保存和在线心跳。"
    };
  }
  if (entryError.value) {
    return {
      title: "还没有成功进入考试",
      copy: "请检查验证码是否正确，或联系 HR 重新发送。"
    };
  }
  return {
    title: "输入验证码后会立即进入考试",
    copy: "系统会加载题目、开始计时，并在答题过程中持续自动保存。"
  };
});
const autosaveStatusLabel = computed(() => {
  if (autosaveState.value === "pending") {
    return "等待保存";
  }
  if (autosaveState.value === "saving") {
    return "保存中";
  }
  if (autosaveState.value === "saved") {
    return "已保存";
  }
  if (autosaveState.value === "error") {
    return "保存异常";
  }
  return "待命";
});
const autosaveStatusCopy = computed(() => autosaveMessage.value);
const autosaveShortCopy = computed(() => {
  if (autosaveState.value === "saving") {
    return "系统正在自动保存你的作答";
  }
  if (autosaveState.value === "saved") {
    return lastAutosaveAt.value ? `最近已保存于 ${lastAutosaveAt.value}` : "你的作答已自动保存";
  }
  if (autosaveState.value === "error") {
    return "自动保存遇到问题，请检查网络后继续";
  }
  return "自动保存中";
});
const autosaveBadgeClass = computed(() => {
  if (autosaveState.value === "error") {
    return "status-badge--danger";
  }
  if (autosaveState.value === "saving" || autosaveState.value === "pending") {
    return "status-badge--warning";
  }
  if (autosaveState.value === "saved") {
    return "status-badge--success";
  }
  return "status-badge--neutral";
});
const heartbeatStatusLabel = computed(() => {
  const intervalSeconds = Math.max(1, Math.round((exam.value?.heartbeatIntervalMs ?? 15000) / 1000));
  return store.lastHeartbeatAt ? `最近心跳 ${store.lastHeartbeatAt}` : `约每 ${intervalSeconds} 秒保活一次`;
});
const recentRiskMessage = computed(() => {
  if (!store.riskEvents.length) {
    return "";
  }
  const latest = store.riskEvents[store.riskEvents.length - 1];
  return `${riskEventLabel(latest.type)}，记录时间 ${formatDateTime(latest.createdAt)}。`;
});
const unansweredQuestionLabels = computed(() => unansweredQuestions.value.map((question) => question.shortLabel).join("、"));

function formatClock(value: string | Date) {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  }).format(typeof value === "string" ? new Date(value) : value);
}

function formatDateTime(value: string | Date) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(typeof value === "string" ? new Date(value) : value);
}

function riskEventLabel(type: string) {
  const mapping: Record<string, string> = {
    window_blur: "检测到窗口失焦",
    page_hidden: "检测到页面被切出前台",
    copy: "检测到复制操作",
    paste: "检测到粘贴操作",
    network_offline: "检测到网络中断",
    network_online: "检测到网络恢复"
  };
  return mapping[type] ?? `检测到 ${type}`;
}

function readLocalDrafts() {
  if (typeof window === "undefined") {
    return {};
  }
  const raw = window.localStorage.getItem(storageKey.value);
  if (!raw) {
    return {};
  }
  try {
    return JSON.parse(raw) as Record<string, Record<string, unknown>>;
  } catch {
    return {};
  }
}

function syncExamSession(payload: PublicExamPayload) {
  const localDrafts = readLocalDrafts();
  store.reset();
  store.setSessionMeta({
    token: payload.token,
    startedAt: payload.startedAt ?? "",
    expiresAt: payload.expiresAt ?? ""
  });
  if (payload.lastHeartbeatAt) {
    store.markHeartbeat(formatClock(payload.lastHeartbeatAt));
  }
  store.hydrateDrafts({
    ...(payload.answers ?? {}),
    ...localDrafts
  });
  if (payload.questions[0]?.id) {
    store.setActiveQuestion(payload.questions[0].id);
  }
  restoreNotice.value = Object.keys(localDrafts).length
    ? `已从当前设备恢复 ${Object.keys(localDrafts).length} 题草稿，系统会继续自动保存。`
    : "";
}

function codeValue(question: ExamQuestion) {
  return String(store.answers[question.id]?.code ?? question.starterCode ?? "");
}

function questionLanguage(question: ExamQuestion) {
  return String(store.answers[question.id]?.language ?? question.language ?? "JavaScript");
}

function questionCompletionState(question: ExamQuestion) {
  const answer = store.answers[question.id] ?? {};

  if (question.kind === "base_info") {
    const fields = question.fields ?? [];
    const filledCount = fields.filter((field) => String(answer[field] ?? "").trim()).length;
    if (!filledCount) {
      return "empty";
    }
    return filledCount === fields.length ? "done" : "partial";
  }

  if (question.kind === "objective") {
    return String(answer.answer ?? "").trim() ? "done" : "empty";
  }

  if (question.kind === "subjective") {
    return String(answer.answer_text ?? "").trim() ? "done" : "empty";
  }

  return String(answer.code ?? "").trim() ? "done" : "empty";
}

function questionCompletionLabel(question: ExamQuestion) {
  const state = questionCompletionState(question);
  if (state === "done") {
    return "已完成";
  }
  if (state === "partial") {
    return "进行中";
  }
  return "未作答";
}

function completionBadgeClass(question: ExamQuestion) {
  const state = questionCompletionState(question);
  if (state === "done") {
    return "status-badge--success";
  }
  if (state === "partial") {
    return "status-badge--warning";
  }
  return "status-badge--neutral";
}

async function loadExamState() {
  loading.value = true;
  loadError.value = "";
  try {
    exam.value = await loadPublicExam(String(route.params.token ?? ""));
    if (exam.value.state === "in_progress") {
      syncExamSession(exam.value);
    } else if (exam.value.state !== "submitted") {
      store.reset();
    }
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "考试信息加载失败，请稍后重试。";
  } finally {
    loading.value = false;
  }
}

async function startExamSession() {
  if (!verificationCode.value.trim()) {
    entryError.value = "请输入验证码。";
    return;
  }

  starting.value = true;
  entryError.value = "";
  try {
    await startPublicExam(String(route.params.token ?? ""), verificationCode.value.trim());
    await loadExamState();
  } catch (error) {
    entryError.value = error instanceof Error ? error.message : "验证码校验失败。";
  } finally {
    starting.value = false;
  }
}

function updateCodeAnswer(questionId: string, code: string) {
  store.upsertDraftAnswer(questionId, { ...(store.answers[questionId] ?? {}), code });
}

function updateCodeLanguage(questionId: string, language: string) {
  const question = questions.value.find((item) => item.id === questionId);
  store.upsertDraftAnswer(questionId, {
    ...(store.answers[questionId] ?? {}),
    language,
    code: question ? codeValue(question) : ""
  });
}

function formatRunResult(result: CodingRunResult) {
  return [
    result.status?.description ? `状态: ${result.status.description}` : "",
    result.stdout ? `stdout:\n${result.stdout}` : "",
    result.stderr ? `stderr:\n${result.stderr}` : "",
    result.compile_output ? `compile_output:\n${result.compile_output}` : ""
  ]
    .filter(Boolean)
    .join("\n\n");
}

async function runActiveCode(question: ExamQuestion) {
  busyMode.value = "run";
  runFeedback.value = {
    questionId: question.id,
    state: "running",
    summary: "系统正在编译并试跑你的代码",
    detail: "试跑不会计分，只会帮助你查看输出、报错和编译状态。"
  };

  try {
    const result = await runCodingQuestion(String(route.params.token ?? ""), {
      language: questionLanguage(question),
      sourceCode: codeValue(question),
      stdin: runInput.value
    });
    runFeedback.value = {
      questionId: question.id,
      state: "success",
      summary: result.stderr || result.compile_output ? "试跑已返回，请先检查报错信息" : "试跑完成，可以根据输出继续调整代码",
      detail: formatRunResult(result) || "本次试跑没有返回额外输出。",
      updatedAt: formatClock(new Date())
    };
  } catch (error) {
    runFeedback.value = {
      questionId: question.id,
      state: "error",
      summary: "试跑失败，请检查网络或代码内容后重试",
      detail: error instanceof Error ? error.message : "试跑失败。",
      updatedAt: formatClock(new Date())
    };
  } finally {
    busyMode.value = null;
  }
}

async function submitActiveCode(question: ExamQuestion) {
  busyMode.value = "submit";
  submitFeedback.value = {
    questionId: question.id,
    state: "running",
    summary: "系统正在进行正式判题",
    detail: "正式提交会按用例判分，并记录为这道代码题的当前结果。"
  };

  try {
    const result = await submitCodingQuestion(String(route.params.token ?? ""), {
      questionId: question.id,
      language: questionLanguage(question),
      sourceCode: codeValue(question)
    });
    submitFeedback.value = {
      questionId: question.id,
      state: "success",
      summary: `通过 ${result.summary.passed_count} / ${result.summary.passed_count + result.summary.failed_count} 个用例`,
      detail: `当前得分 ${result.summary.total_score} / ${result.summary.max_score}`,
      updatedAt: formatClock(new Date()),
      passedCount: result.summary.passed_count,
      failedCount: result.summary.failed_count,
      totalScore: result.summary.total_score,
      maxScore: result.summary.max_score,
      cases: result.results.map((item, index) => ({
        index: index + 1,
        passed: item.passed,
        score: item.score,
        stdin: item.stdin.trim(),
        expected: item.expected_stdout.trim(),
        actual: item.actual_stdout.trim(),
        status: item.status?.description ?? (item.passed ? "通过" : "未通过")
      }))
    };
  } catch (error) {
    submitFeedback.value = {
      questionId: question.id,
      state: "error",
      summary: "正式提交失败，请稍后重试",
      detail: error instanceof Error ? error.message : "代码提交失败。",
      updatedAt: formatClock(new Date())
    };
  } finally {
    busyMode.value = null;
  }
}

function openSubmitConfirm() {
  showSubmitConfirm.value = true;
  submitError.value = "";
}

function closeSubmitConfirm() {
  showSubmitConfirm.value = false;
  submitError.value = "";
}

async function submitCurrentExam() {
  submittingExam.value = true;
  submitError.value = "";
  try {
    await submitExam(String(route.params.token ?? ""));
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(storageKey.value);
    }
    showSubmitConfirm.value = false;
    await loadExamState();
  } catch (error) {
    submitError.value = error instanceof Error ? error.message : "交卷失败，请稍后重试。";
  } finally {
    submittingExam.value = false;
  }
}

async function reportRisk(eventType: string, payload: Record<string, unknown> = {}) {
  if (exam.value?.state !== "in_progress") {
    return;
  }
  store.logRiskEvent(eventType);
  await sendRiskEvent(String(route.params.token ?? ""), eventType, payload);
}

const handleBlur = () => void reportRisk("window_blur");
const handleVisibilityChange = () => {
  if (document.visibilityState === "hidden") {
    void reportRisk("page_hidden");
  }
};
const handleCopy = () => void reportRisk("copy");
const handlePaste = () => void reportRisk("paste");
const handleOffline = () => {
  connectionStatus.value = "offline";
  networkNotice.value = "系统会先把答案保存在当前设备，恢复网络后继续同步和发送心跳。";
  void reportRisk("network_offline");
};
const handleOnline = () => {
  connectionStatus.value = "online";
  networkNotice.value = "连接已恢复，系统会继续同步答案和在线状态。";
  void reportRisk("network_online");
};

watch(
  () => route.params.token,
  async () => {
    await loadExamState();
  },
  { immediate: true }
);

watch(
  () => store.answers,
  () => {
    if (exam.value?.state !== "in_progress") {
      return;
    }
    autosaveState.value = "pending";
    autosaveMessage.value =
      connectionStatus.value === "offline" ? "离线中，答案已写入本机，待网络恢复后继续同步。" : "检测到作答变化，系统准备自动保存。";
  },
  { deep: true }
);

watch(
  () => activeQuestion.value?.id,
  () => {
    runFeedback.value = null;
    submitFeedback.value = null;
  }
);

onMounted(() => {
  clockTimer = window.setInterval(() => {
    nowMs.value = Date.now();
  }, 1000);

  window.addEventListener("blur", handleBlur);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  document.addEventListener("copy", handleCopy);
  document.addEventListener("paste", handlePaste);
  window.addEventListener("offline", handleOffline);
  window.addEventListener("online", handleOnline);
});

onBeforeUnmount(() => {
  window.clearInterval(clockTimer);
  window.removeEventListener("blur", handleBlur);
  document.removeEventListener("visibilitychange", handleVisibilityChange);
  document.removeEventListener("copy", handleCopy);
  document.removeEventListener("paste", handlePaste);
  window.removeEventListener("offline", handleOffline);
  window.removeEventListener("online", handleOnline);
});

useAutosave(
  () => store.answers,
  async (value) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(storageKey.value, JSON.stringify(value));
    }

    if (exam.value?.state !== "in_progress") {
      return;
    }

    if (connectionStatus.value === "offline") {
      autosaveState.value = "saved";
      autosaveMessage.value = "当前处于离线状态，答案已保存在本机，联网后会继续同步。";
      lastAutosaveAt.value = formatClock(new Date());
      return;
    }

    autosaveState.value = "saving";
    autosaveMessage.value = "系统正在自动保存并同步你的作答。";

    try {
      await Promise.all(
        Object.entries(value).map(async ([questionId, draftAnswer]) => {
          await saveDraftAnswer(String(route.params.token ?? ""), questionId, draftAnswer as Record<string, unknown>);
        })
      );
      autosaveState.value = "saved";
      autosaveMessage.value = "答案已自动保存，可以继续安心作答。";
      lastAutosaveAt.value = formatClock(new Date());
    } catch (error) {
      autosaveState.value = "error";
      autosaveMessage.value = error instanceof Error ? error.message : "自动保存失败，请检查网络后继续作答。";
    }
  }
);

useHeartbeat(async () => {
  if (exam.value?.state !== "in_progress" || connectionStatus.value === "offline") {
    return;
  }
  await sendHeartbeat(String(route.params.token ?? ""));
  store.markHeartbeat(formatClock(new Date()));
}, 15000);
</script>

<style scoped>
.state-card,
.gate-card,
.submitted-card {
  max-width: 960px;
  margin: 0 auto;
  padding: 28px;
}

.state-btn {
  margin-top: 20px;
}

.gate-hero {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.9fr);
  gap: 24px;
  align-items: start;
}

.gate-title {
  margin: 18px 0 0;
  font-size: clamp(2rem, 5vw, 3rem);
  letter-spacing: -0.05em;
}

.gate-metric-grid,
.confirm-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.gate-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(280px, 0.8fr);
  gap: 20px;
  margin-top: 28px;
}

.gate-section,
.gate-side-card {
  display: grid;
  gap: 16px;
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(20, 33, 61, 0.06);
}

.gate-side-card__title {
  font-size: 1rem;
  font-weight: 700;
}

.instruction-list,
.gate-status-list {
  display: grid;
  gap: 12px;
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.7;
}

.instruction-list {
  padding-left: 18px;
}

.gate-status-item {
  display: grid;
  gap: 4px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.04);
}

.gate-field {
  display: grid;
  gap: 8px;
  margin-top: 24px;
  color: var(--ink-soft);
}

.gate-feedback {
  display: grid;
  gap: 6px;
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
  color: var(--ink-soft);
}

.gate-feedback--active {
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent-strong);
}

.gate-btn {
  margin-top: 18px;
}

.error-banner {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(220, 38, 38, 0.1);
  color: var(--danger);
}

.exam-layout {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 24px;
}

.exam-sidebar {
  position: sticky;
  top: 24px;
  display: grid;
  gap: 18px;
  height: fit-content;
  padding: 24px;
}

.sidebar-head-wrap {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.sidebar-head {
  margin: 16px 0 0;
  font-size: 2rem;
  letter-spacing: -0.05em;
}

.progress-card,
.status-card {
  display: grid;
  gap: 12px;
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(20, 33, 61, 0.06);
}

.progress-card__head,
.status-card__head,
.intro-head,
.intro-meta,
.status-card__meta,
.session-inline-meta,
.nav-button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.progress-copy,
.status-copy,
.session-meta,
.nav-copy small {
  color: var(--ink-soft);
}

.progress-track {
  overflow: hidden;
  height: 10px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.08);
}

.progress-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--accent) 0%, #14b8a6 100%);
}

.session-block {
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.14), rgba(249, 115, 22, 0.12));
}

.timer-value {
  font-size: 2.6rem;
  font-weight: 700;
  letter-spacing: -0.06em;
}

.session-inline-meta {
  margin-top: 12px;
  flex-wrap: wrap;
  color: var(--ink-soft);
  font-size: 0.92rem;
}

.alert-stack {
  display: grid;
  gap: 10px;
}

.alert-banner {
  display: grid;
  gap: 4px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.06);
}

.alert-banner--info {
  background: rgba(59, 130, 246, 0.1);
}

.alert-banner--success {
  background: rgba(15, 118, 110, 0.12);
}

.alert-banner--warning {
  background: rgba(245, 158, 11, 0.14);
}

.alert-banner--danger {
  background: rgba(220, 38, 38, 0.1);
}

.exam-nav {
  display: grid;
  gap: 10px;
}

.nav-item {
  padding: 14px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
  font-weight: 600;
}

.nav-button {
  width: 100%;
  border: 0;
  cursor: pointer;
}

.nav-copy {
  display: grid;
  gap: 4px;
  text-align: left;
}

.nav-copy small {
  font-size: 0.78rem;
}

.nav-meta {
  display: grid;
  gap: 4px;
  justify-items: end;
  text-align: right;
}

.nav-meta em {
  font-style: normal;
  font-size: 0.8rem;
}

.nav-item--active {
  color: var(--accent-strong);
  background: rgba(15, 118, 110, 0.1);
  box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.14);
}

.nav-item--done {
  border-color: rgba(15, 118, 110, 0.2);
}

.nav-item--partial {
  border-color: rgba(245, 158, 11, 0.2);
}

.session-meta {
  display: grid;
  gap: 8px;
  font-size: 0.92rem;
}

.submit-btn {
  width: 100%;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  white-space: nowrap;
}

.status-badge--neutral {
  background: rgba(20, 33, 61, 0.08);
  color: var(--ink-strong);
}

.status-badge--success {
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent-strong);
}

.status-badge--warning {
  background: rgba(245, 158, 11, 0.14);
  color: #9a6700;
}

.status-badge--danger {
  background: rgba(220, 38, 38, 0.12);
  color: var(--danger);
}

.exam-main {
  display: grid;
  gap: 20px;
}

.intro-card {
  padding: 24px;
}

.intro-badges,
.intro-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.intro-meta {
  margin-top: 18px;
  color: var(--ink-soft);
  font-size: 0.92rem;
}

.exam-notice-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
}

.notice-card {
  padding: 16px 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(20, 33, 61, 0.06);
}

.notice-card p {
  margin: 8px 0 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

.notice-card--success {
  border-color: rgba(15, 118, 110, 0.14);
}

.notice-card--warning {
  border-color: rgba(245, 158, 11, 0.2);
}

.notice-card--danger {
  border-color: rgba(220, 38, 38, 0.18);
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 20px;
  background: rgba(15, 23, 42, 0.32);
  z-index: 20;
}

.submit-modal {
  width: min(640px, 100%);
  padding: 26px;
}

.confirm-warning {
  display: grid;
  gap: 6px;
  margin-top: 20px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(245, 158, 11, 0.14);
  color: #9a6700;
}

.confirm-alert {
  margin-top: 18px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

@media (max-width: 1100px) {
  .exam-layout {
    grid-template-columns: 1fr;
  }

  .exam-sidebar {
    position: static;
  }
}

@media (max-width: 860px) {
  .gate-hero,
  .gate-layout,
  .gate-metric-grid,
  .confirm-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .sidebar-head-wrap,
  .progress-card__head,
  .status-card__head,
  .status-card__meta,
  .intro-head,
  .modal-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .nav-button {
    align-items: flex-start;
    flex-direction: column;
  }

  .nav-meta {
    justify-items: start;
    text-align: left;
  }

  .timer-value {
    font-size: 2.2rem;
  }
}
</style>
