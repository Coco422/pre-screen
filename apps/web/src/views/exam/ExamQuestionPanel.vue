<template>
  <article class="glass-card question-panel">
    <header class="question-panel__head">
      <div class="question-panel__headline">
        <div class="question-panel__eyebrow">
          <span class="question-panel__type">{{ question.typeLabel }}</span>
          <span class="question-panel__progress">{{ progressLabel }}</span>
        </div>
        <h3>{{ question.title }}</h3>
      </div>
      <span class="pill">{{ question.score }} 分</span>
    </header>

    <p class="section-copy">{{ question.description }}</p>

    <div class="question-status-bar">
      <span>当前状态：{{ completionLabel }}</span>
      <span>自动保存：{{ autosaveLabel }}</span>
    </div>

    <p class="question-hint">{{ helperCopy }}</p>

    <div v-if="question.mode === 'base_info'" class="field-grid">
      <label v-for="field in question.fields" :key="field" class="field-item">
        <span>{{ field }}</span>
        <input
          class="soft-input"
          :value="stringValue(field)"
          :placeholder="`填写${field}`"
          @input="updateField(field, ($event.target as HTMLInputElement).value)"
        />
      </label>
    </div>

    <div v-else-if="question.mode === 'objective'" class="choice-grid">
      <button
        v-for="option in question.options"
        :key="option"
        class="choice-pill"
        :class="{ 'choice-pill--active': option === selectedOption }"
        @click="selectOption(option)"
      >
        {{ option }}
      </button>
    </div>

    <textarea
      v-else
      class="soft-textarea"
      :value="textValue"
      placeholder="请输入你的回答"
      @input="updateText(($event.target as HTMLTextAreaElement).value)"
    />
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  question: {
    id: string;
    title: string;
    description: string;
    score: number;
    typeLabel: string;
    mode: "base_info" | "objective" | "subjective";
    fields?: string[];
    options?: string[];
  };
  modelValue?: Record<string, unknown>;
  progressLabel?: string;
  completionLabel?: string;
  autosaveLabel?: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: Record<string, unknown>];
}>();

const stringValue = (field: string) => String(props.modelValue?.[field] ?? "");
const selectedOption = computed(() => String(props.modelValue?.answer ?? ""));
const textValue = computed(() => String(props.modelValue?.answer_text ?? ""));
const helperCopy = computed(() => {
  if (props.question.mode === "base_info") {
    return "这部分信息会随填写自动保存，建议一次把字段补齐，避免遗漏基础资料。";
  }
  if (props.question.mode === "objective") {
    return "点击选项即可记录答案；切换答案后系统会自动更新保存状态。";
  }
  return "主观题支持自由作答，输入过程中系统会自动保存，不需要手动提交本题。";
});

function updateField(field: string, value: string) {
  emit("update:modelValue", { ...(props.modelValue ?? {}), [field]: value });
}

function selectOption(option: string) {
  emit("update:modelValue", { answer: option });
}

function updateText(value: string) {
  emit("update:modelValue", { answer_text: value });
}
</script>

<style scoped>
.question-panel {
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
  gap: 10px;
  align-items: center;
}

.question-panel__type {
  color: var(--accent-strong);
  font-weight: 700;
  font-size: 0.85rem;
}

.question-panel__progress {
  color: var(--ink-soft);
  font-size: 0.85rem;
}

.question-status-bar {
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

.question-hint {
  margin: 14px 0 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.field-item {
  display: grid;
  gap: 8px;
  color: var(--ink-soft);
}

.choice-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
}

.choice-pill {
  border: 1px solid rgba(20, 33, 61, 0.1);
  background: rgba(255, 255, 255, 0.82);
  border-radius: 999px;
  padding: 12px 16px;
  cursor: pointer;
  transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
}

.choice-pill:hover {
  transform: translateY(-1px);
}

.choice-pill--active {
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent-strong);
  border-color: rgba(15, 118, 110, 0.24);
}

@media (max-width: 720px) {
  .field-grid {
    grid-template-columns: 1fr;
  }

  .question-panel__head {
    flex-direction: column;
  }
}
</style>
