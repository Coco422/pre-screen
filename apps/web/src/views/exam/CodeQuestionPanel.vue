<template>
  <article class="glass-card code-panel">
    <header class="question-panel__head">
      <div class="question-panel__headline">
        <div class="question-panel__eyebrow">
          <div class="question-panel__type">代码题</div>
          <span class="question-panel__progress">{{ progressLabel }}</span>
        </div>
        <h3>{{ title }}</h3>
      </div>
      <span class="pill">{{ score }} 分</span>
    </header>

    <p class="section-copy">{{ description }}</p>

    <div class="code-status-bar">
      <span>自动保存：{{ autosaveLabel }}</span>
      <span>试跑不计分，正式提交会按用例判题并更新当前结果</span>
    </div>

    <div class="code-toolbar">
      <label class="language-picker">
        <span class="metric-label">运行语言</span>
        <select class="soft-select code-select" :value="language" @change="$emit('update:language', ($event.target as HTMLSelectElement).value)">
          <option v-for="item in supportedLanguages" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>

      <div class="code-toolbar__copy">
        <strong>操作说明</strong>
        <span>先试跑确认输出，再执行正式提交查看判题结果。</span>
      </div>
    </div>

    <textarea
      class="code-editor"
      :value="code"
      placeholder="在这里输入代码..."
      spellcheck="false"
      @input="$emit('update:code', ($event.target as HTMLTextAreaElement).value)"
    />

    <div class="stdin-panel">
      <label class="metric-label" for="stdin-input">试跑输入</label>
      <textarea
        id="stdin-input"
        class="soft-textarea stdin-input"
        :value="runInput"
        placeholder='例如: [1,1,2,3,2]'
        @input="$emit('update:runInput', ($event.target as HTMLTextAreaElement).value)"
      />
    </div>

    <div class="code-actions">
      <button class="secondary-btn" :disabled="busyMode === 'run'" @click="$emit('run')">
        {{ busyMode === "run" ? "系统正在试跑..." : "试跑代码" }}
      </button>
      <button class="primary-btn" :disabled="busyMode === 'submit'" @click="$emit('submit')">
        {{ busyMode === "submit" ? "系统正在判题..." : "正式提交判题" }}
      </button>
    </div>

    <div class="feedback-grid">
      <section class="feedback-card" :class="feedbackCardClass(runFeedback?.state)">
        <div class="feedback-card__head">
          <strong>试跑反馈</strong>
          <span class="feedback-state">{{ feedbackStateLabel(runFeedback?.state, '等待试跑') }}</span>
        </div>
        <p class="feedback-summary">{{ runFeedback?.summary ?? "点击“试跑代码”后，这里会显示编译、输出或报错反馈。" }}</p>
        <div v-if="runFeedback?.updatedAt" class="feedback-meta">最近更新 {{ runFeedback.updatedAt }}</div>
        <pre v-if="runFeedback?.detail" class="result-output">{{ runFeedback.detail }}</pre>
      </section>

      <section class="feedback-card" :class="feedbackCardClass(submitFeedback?.state)">
        <div class="feedback-card__head">
          <strong>正式提交反馈</strong>
          <span class="feedback-state">{{ feedbackStateLabel(submitFeedback?.state, '等待判题') }}</span>
        </div>
        <p class="feedback-summary">{{ submitFeedback?.summary ?? "点击“正式提交判题”后，这里会显示通过用例数、得分和逐条判题结果。" }}</p>
        <div v-if="submitFeedback?.detail" class="feedback-meta">{{ submitFeedback.detail }}</div>
        <div v-if="submitFeedback?.updatedAt" class="feedback-meta">最近更新 {{ submitFeedback.updatedAt }}</div>

        <div v-if="submitFeedback?.state === 'success' && submitFeedback.cases?.length" class="judge-metrics">
          <article class="metric-tile">
            <div class="metric-value">{{ submitFeedback.passedCount ?? 0 }}</div>
            <div class="metric-label">通过用例</div>
          </article>
          <article class="metric-tile">
            <div class="metric-value">{{ submitFeedback.failedCount ?? 0 }}</div>
            <div class="metric-label">未通过用例</div>
          </article>
          <article class="metric-tile">
            <div class="metric-value">{{ submitFeedback.totalScore ?? 0 }}</div>
            <div class="metric-label">当前得分</div>
          </article>
        </div>

        <div v-if="submitFeedback?.cases?.length" class="case-list">
          <article
            v-for="item in submitFeedback.cases"
            :key="item.index"
            class="case-item"
            :class="{ 'case-item--pass': item.passed, 'case-item--fail': !item.passed }"
          >
            <div class="case-item__head">
              <strong>用例 {{ item.index }}</strong>
              <span>{{ item.status }} · {{ item.score }} 分</span>
            </div>
            <div class="case-item__detail">输入：{{ item.stdin || "(空)" }}</div>
            <div class="case-item__detail">期望：{{ item.expected || "(空)" }}</div>
            <div class="case-item__detail">实际：{{ item.actual || "(空)" }}</div>
          </article>
        </div>
      </section>
    </div>
  </article>
</template>

<script setup lang="ts">
type FeedbackState = "idle" | "running" | "success" | "error";

type RunFeedback = {
  state: FeedbackState;
  summary: string;
  detail?: string;
  updatedAt?: string;
};

type SubmitFeedback = {
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

defineProps<{
  title: string;
  description: string;
  language: string;
  supportedLanguages: string[];
  score: number;
  code: string;
  runInput: string;
  busyMode?: "run" | "submit" | null;
  progressLabel?: string;
  autosaveLabel?: string;
  runFeedback?: RunFeedback;
  submitFeedback?: SubmitFeedback;
}>();

defineEmits<{
  "update:code": [value: string];
  "update:language": [value: string];
  "update:runInput": [value: string];
  run: [];
  submit: [];
}>();

function feedbackStateLabel(state: FeedbackState | undefined, fallback: string) {
  if (state === "running") {
    return "进行中";
  }
  if (state === "success") {
    return "已返回";
  }
  if (state === "error") {
    return "需处理";
  }
  return fallback;
}

function feedbackCardClass(state: FeedbackState | undefined) {
  if (state === "running") {
    return "feedback-card--warning";
  }
  if (state === "success") {
    return "feedback-card--success";
  }
  if (state === "error") {
    return "feedback-card--danger";
  }
  return "";
}
</script>

<style scoped>
.code-panel {
  padding: 24px;
}

.question-panel__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.question-panel__headline {
  display: grid;
  gap: 10px;
}

.question-panel__eyebrow {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.question-panel__type {
  color: var(--warm);
  font-weight: 700;
  font-size: 0.85rem;
}

.question-panel__progress {
  color: var(--ink-soft);
  font-size: 0.85rem;
}

.code-status-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 18px;
  margin-top: 18px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
  color: var(--ink-soft);
  font-size: 0.9rem;
}

.code-toolbar,
.code-actions,
.feedback-card__head,
.case-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.code-toolbar {
  margin-top: 20px;
}

.code-toolbar__copy {
  display: grid;
  gap: 4px;
  color: var(--ink-soft);
}

.language-picker {
  display: grid;
  gap: 8px;
}

.code-select {
  min-width: 180px;
}

.code-editor {
  width: 100%;
  min-height: 320px;
  margin-top: 18px;
  padding: 18px;
  border: 1px solid rgba(20, 33, 61, 0.12);
  border-radius: 22px;
  background: linear-gradient(180deg, #101827 0%, #172134 100%);
  color: #eff6ff;
  font-family: "SFMono-Regular", "JetBrains Mono", "Menlo", monospace;
  font-size: 0.95rem;
  line-height: 1.7;
  resize: vertical;
}

.stdin-panel {
  margin-top: 18px;
}

.stdin-input {
  min-height: 110px;
  margin-top: 8px;
}

.code-actions {
  margin-top: 20px;
}

.feedback-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.feedback-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.feedback-card--success {
  border-color: rgba(15, 118, 110, 0.18);
}

.feedback-card--warning {
  border-color: rgba(245, 158, 11, 0.2);
}

.feedback-card--danger {
  border-color: rgba(220, 38, 38, 0.18);
}

.feedback-state,
.feedback-meta,
.feedback-summary {
  color: var(--ink-soft);
}

.feedback-summary,
.feedback-meta,
.case-item__detail {
  line-height: 1.6;
}

.judge-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.case-list {
  display: grid;
  gap: 12px;
}

.case-item {
  padding: 14px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.04);
}

.case-item--pass {
  box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.14);
}

.case-item--fail {
  box-shadow: inset 0 0 0 1px rgba(220, 38, 38, 0.12);
}

.result-output {
  margin: 0;
  padding: 14px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
  white-space: pre-wrap;
  word-break: break-word;
}

@media (max-width: 900px) {
  .feedback-grid,
  .judge-metrics {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .question-panel__head {
    flex-direction: column;
  }
}
</style>
