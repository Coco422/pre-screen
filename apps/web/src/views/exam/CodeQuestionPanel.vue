<template>
  <article class="glass-card code-panel">
    <header class="question-panel__head">
      <div>
        <div class="question-panel__type">代码题</div>
        <h3>{{ title }}</h3>
      </div>
      <span class="pill">{{ score }} 分</span>
    </header>

    <p class="section-copy">{{ description }}</p>

    <div class="code-toolbar">
      <label class="language-picker">
        <span class="metric-label">运行语言</span>
        <select class="soft-select code-select" :value="language" @change="$emit('update:language', ($event.target as HTMLSelectElement).value)">
          <option v-for="item in supportedLanguages" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>
      <span class="section-copy">支持试跑与正式提交</span>
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
        {{ busyMode === "run" ? "试跑中..." : "试跑" }}
      </button>
      <button class="primary-btn" :disabled="busyMode === 'submit'" @click="$emit('submit')">
        {{ busyMode === "submit" ? "提交中..." : "提交判题" }}
      </button>
    </div>

    <div v-if="runResult || submitSummary" class="result-card">
      <div v-if="runResult" class="result-block">
        <div class="metric-label">试跑结果</div>
        <pre class="result-output">{{ runResult }}</pre>
      </div>
      <div v-if="submitSummary" class="result-block">
        <div class="metric-label">判题摘要</div>
        <pre class="result-output">{{ submitSummary }}</pre>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
  language: string;
  supportedLanguages: string[];
  score: number;
  code: string;
  runInput: string;
  runResult?: string;
  submitSummary?: string;
  busyMode?: "run" | "submit" | null;
}>();

defineEmits<{
  "update:code": [value: string];
  "update:language": [value: string];
  "update:runInput": [value: string];
  run: [];
  submit: [];
}>();
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

.question-panel__type {
  color: var(--warm);
  font-weight: 700;
  font-size: 0.85rem;
}

.code-toolbar,
.code-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 20px;
  flex-wrap: wrap;
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

.result-card {
  margin-top: 20px;
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.84);
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.result-block + .result-block {
  margin-top: 16px;
}

.result-output {
  margin: 8px 0 0;
  padding: 14px;
  border-radius: 16px;
  background: rgba(20, 33, 61, 0.05);
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
