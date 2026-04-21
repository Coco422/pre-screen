<template>
  <article class="glass-card question-panel">
    <header class="question-panel__head">
      <div>
        <div class="question-panel__type">{{ question.typeLabel }}</div>
        <h3>{{ question.title }}</h3>
      </div>
      <span class="pill">{{ question.score }} 分</span>
    </header>

    <p class="section-copy">{{ question.description }}</p>

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
}>();

const emit = defineEmits<{
  "update:modelValue": [value: Record<string, unknown>];
}>();

const stringValue = (field: string) => String(props.modelValue?.[field] ?? "");
const selectedOption = computed(() => String(props.modelValue?.value ?? ""));
const textValue = computed(() => String(props.modelValue?.value ?? ""));

function updateField(field: string, value: string) {
  emit("update:modelValue", { ...(props.modelValue ?? {}), [field]: value });
}

function selectOption(option: string) {
  emit("update:modelValue", { value: option });
}

function updateText(value: string) {
  emit("update:modelValue", { value });
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

.question-panel__type {
  color: var(--accent-strong);
  font-weight: 700;
  font-size: 0.85rem;
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
}
</style>
