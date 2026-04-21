<template>
  <div class="shell-page exam-page">
    <div class="exam-layout">
      <aside class="glass-card exam-sidebar">
        <div>
          <div class="pill">Candidate Session</div>
          <h1 class="sidebar-head">{{ exam?.paperTitle ?? "技术岗在线考核" }}</h1>
          <p class="section-copy">自动保存已启用，后端心跳为准。切页、失焦等轻量风控事件会记录。</p>
        </div>

        <div class="session-block">
          <div class="timer-value">{{ countdownLabel }}</div>
          <div class="metric-label">剩余时间</div>
        </div>

        <div class="nav-stack exam-nav">
          <button
            v-for="question in questions"
            :key="question.id"
            class="nav-item nav-button"
            :class="{ 'nav-item--active': store.activeQuestionId === question.id }"
            @click="store.setActiveQuestion(question.id)"
          >
            <span>{{ question.shortLabel }}</span>
            <strong>{{ question.score }} 分</strong>
          </button>
        </div>

        <div class="session-meta">
          <div>最后心跳：{{ store.lastHeartbeatAt || "等待中" }}</div>
          <div>本地草稿：{{ savedDraftCount }} 题</div>
        </div>
      </aside>

      <main class="exam-main">
        <section class="glass-card intro-card">
          <div class="pill">Exam Flow</div>
          <h2 class="section-title">先补基础信息，再完成客观题、主观题和代码题。</h2>
          <p class="section-copy">
            这不是冷冰冰的表单页。我们尽量把作答过程做得安静、清晰、少打扰，同时保留必要的稳定性和风控记录。
          </p>
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
          :run-result="runResult"
          :submit-summary="submitResult"
          :busy-mode="busyMode"
          @update:code="updateCodeAnswer(activeQuestion.id, $event)"
          @update:language="updateCodeLanguage(activeQuestion.id, $event)"
          @update:run-input="runInput = $event"
          @run="runActiveCode(activeQuestion)"
          @submit="submitActiveCode(activeQuestion)"
        />

        <section v-else class="glass-card intro-card">
          <div class="pill">Exam Flow</div>
          <h2 class="section-title">正在准备考卷内容...</h2>
          <p class="section-copy">题目会优先从 Gateway 加载，异常时回退到本地兜底数据。</p>
        </section>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useRoute } from "vue-router";

import { useAutosave } from "../../composables/useAutosave";
import { useHeartbeat } from "../../composables/useHeartbeat";
import {
  loadExamShell,
  runCodingQuestion,
  saveDraftAnswer,
  sendHeartbeat,
  sendRiskEvent,
  submitCodingQuestion,
  type CodingRunResult,
  type CodingSubmitResult,
  type ExamQuestion,
  type ExamShellPayload
} from "../../lib/gateway";
import { useExamSessionStore } from "../../stores/examSession";
import CodeQuestionPanel from "./CodeQuestionPanel.vue";
import ExamQuestionPanel from "./ExamQuestionPanel.vue";

const route = useRoute();
const store = useExamSessionStore();
const storageKey = computed(() => `pre-screen:drafts:${route.params.token as string}`);
const defaultCode = "function unique(items) {\n  return [...new Set(items)];\n}";
const exam = ref<ExamShellPayload | null>(null);
const questions = computed(() => exam.value?.questions ?? []);
const runInput = ref("[1,1,2,3,2]");
const busyMode = ref<"run" | "submit" | null>(null);
const runResult = ref("");
const submitResult = ref("");

const activeQuestion = computed(() => {
  return questions.value.find((question) => question.id === store.activeQuestionId) ?? questions.value[0];
});

const savedDraftCount = computed(() => Object.keys(store.answers).length);
const countdownLabel = computed(() => {
  if (!store.expiresAt) {
    return "90:00";
  }
  const diff = new Date(store.expiresAt).getTime() - Date.now();
  const totalSeconds = Math.max(0, Math.floor(diff / 1000));
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
});

function codeValue(question: ExamQuestion) {
  return String(store.answers[question.id]?.code ?? question.starterCode ?? defaultCode);
}

function updateCodeAnswer(questionId: string, code: string) {
  store.upsertDraftAnswer(questionId, {
    ...(store.answers[questionId] ?? {}),
    code
  });
}

function questionLanguage(question: ExamQuestion) {
  return String(store.answers[question.id]?.language ?? question.language ?? "JavaScript");
}

function updateCodeLanguage(questionId: string, language: string) {
  const current = store.answers[questionId] ?? {};
  store.upsertDraftAnswer(questionId, {
    ...current,
    language,
    code: typeof current.code === "string" ? current.code : ""
  });
}

function formatRunResult(result: CodingRunResult) {
  const parts = [
    result.status?.description ? `状态: ${result.status.description}` : "",
    result.stdout ? `stdout:\n${result.stdout}` : "",
    result.stderr ? `stderr:\n${result.stderr}` : "",
    result.compile_output ? `compile_output:\n${result.compile_output}` : ""
  ].filter(Boolean);
  return parts.join("\n\n");
}

function formatSubmitResult(result: CodingSubmitResult) {
  const lines = [
    `通过 ${result.summary.passed_count} / ${result.summary.passed_count + result.summary.failed_count}`,
    `得分 ${result.summary.total_score} / ${result.summary.max_score}`
  ];

  result.results.forEach((item, index) => {
    lines.push(
      `用例 ${index + 1}: ${item.passed ? "通过" : "未通过"} | 输入 ${item.stdin.trim()} | 期望 ${item.expected_stdout.trim()} | 实际 ${item.actual_stdout.trim()}`
    );
  });

  return lines.join("\n");
}

async function runActiveCode(question: ExamQuestion) {
  busyMode.value = "run";
  try {
    const result = await runCodingQuestion(String(route.params.token ?? ""), {
      language: questionLanguage(question),
      sourceCode: codeValue(question),
      stdin: runInput.value
    });
    runResult.value = formatRunResult(result);
  } catch (error) {
    runResult.value = `试跑失败: ${error instanceof Error ? error.message : String(error)}`;
  } finally {
    busyMode.value = null;
  }
}

async function submitActiveCode(question: ExamQuestion) {
  busyMode.value = "submit";
  try {
    const result = await submitCodingQuestion(String(route.params.token ?? ""), {
      questionId: question.id,
      language: questionLanguage(question),
      sourceCode: codeValue(question)
    });
    submitResult.value = formatSubmitResult(result);
  } catch (error) {
    submitResult.value = `提交失败: ${error instanceof Error ? error.message : String(error)}`;
  } finally {
    busyMode.value = null;
  }
}

async function reportRisk(eventType: string, payload: Record<string, unknown> = {}) {
  store.logRiskEvent(eventType);
  await sendRiskEvent(String(route.params.token ?? ""), eventType, payload);
}

const handleBlur = () => {
  void reportRisk("window_blur");
};

const handleVisibilityChange = () => {
  if (document.visibilityState === "hidden") {
    void reportRisk("page_hidden");
  }
};

const handleCopy = () => {
  void reportRisk("copy");
};

const handlePaste = () => {
  void reportRisk("paste");
};

const handleOffline = () => {
  void reportRisk("network_offline");
};

const handleOnline = () => {
  void reportRisk("network_online");
};

onMounted(async () => {
  const token = String(route.params.token ?? "");
  exam.value = await loadExamShell(token);
  const now = new Date();
  store.setSessionMeta({
    token,
    startedAt: now.toISOString(),
    expiresAt: new Date(now.getTime() + (exam.value?.durationMinutes ?? 90) * 60 * 1000).toISOString()
  });

  const cached = window.localStorage.getItem(storageKey.value);
  if (cached) {
    store.hydrateDrafts(JSON.parse(cached) as Record<string, Record<string, unknown>>);
  }

  window.addEventListener("blur", handleBlur);
  document.addEventListener("visibilitychange", handleVisibilityChange);
  document.addEventListener("copy", handleCopy);
  document.addEventListener("paste", handlePaste);
  window.addEventListener("offline", handleOffline);
  window.addEventListener("online", handleOnline);
});

onBeforeUnmount(() => {
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
    window.localStorage.setItem(storageKey.value, JSON.stringify(value));
    await Promise.all(
      Object.entries(value).map(async ([questionId, draftAnswer]) => {
        await saveDraftAnswer(
          String(route.params.token ?? ""),
          questionId,
          draftAnswer as Record<string, unknown>
        );
      })
    );
  }
);

useHeartbeat(async () => {
  await sendHeartbeat(String(route.params.token ?? ""));
  store.markHeartbeat(new Date().toLocaleTimeString("zh-CN", { hour12: false }));
}, 15000);
</script>

<style scoped>
.exam-page {
  position: relative;
  overflow: hidden;
}

.exam-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 24px;
}

.exam-sidebar {
  position: sticky;
  top: 24px;
  height: fit-content;
  padding: 24px;
}

.sidebar-head {
  margin: 16px 0 0;
  font-size: 2rem;
  letter-spacing: -0.05em;
}

.session-block {
  margin: 26px 0;
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.14), rgba(249, 115, 22, 0.12));
}

.timer-value {
  font-size: 2.8rem;
  font-weight: 700;
  letter-spacing: -0.06em;
}

.exam-nav .nav-item {
  background: rgba(255, 255, 255, 0.75);
}

.nav-button {
  display: flex;
  justify-content: space-between;
  width: 100%;
  border: 0;
  cursor: pointer;
}

.nav-item--active {
  color: var(--accent-strong);
  background: rgba(15, 118, 110, 0.12);
}

.session-meta {
  margin-top: 20px;
  display: grid;
  gap: 8px;
  color: var(--ink-soft);
  font-size: 0.9rem;
}

.exam-main {
  display: grid;
  gap: 18px;
}

.intro-card {
  padding: 24px;
}

@media (max-width: 960px) {
  .exam-layout {
    grid-template-columns: 1fr;
  }

  .exam-sidebar {
    position: static;
  }
}
</style>
