<template>
  <article class="score-card">
    <div class="score-head">
      <div>
        <div class="score-title">{{ label }}</div>
        <div v-if="detail" class="score-detail">{{ detail }}</div>
      </div>
      <div class="score-value">{{ value }}</div>
    </div>
    <div class="score-track">
      <div class="score-fill" :class="`score-fill--${tone}`" :style="{ width: `${safePercent}%` }"></div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    label: string;
    value: string | number;
    percent: number;
    detail?: string;
    tone?: "neutral" | "info" | "success" | "warning" | "danger";
  }>(),
  {
    detail: "",
    tone: "neutral"
  }
);

const safePercent = computed(() => Math.min(100, Math.max(0, Math.round(props.percent))));
</script>

<style scoped>
.score-card {
  display: grid;
  gap: 10px;
}

.score-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.score-title {
  font-size: 0.92rem;
  color: var(--ink-soft);
}

.score-detail {
  margin-top: 4px;
  font-size: 0.82rem;
  line-height: 1.5;
  color: var(--ink-soft);
}

.score-value {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--ink-base);
}

.score-track {
  overflow: hidden;
  height: 8px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.08);
}

.score-fill {
  height: 100%;
  border-radius: inherit;
}

.score-fill--neutral {
  background: rgba(71, 85, 105, 0.88);
}

.score-fill--info {
  background: rgba(14, 116, 144, 0.88);
}

.score-fill--success {
  background: rgba(22, 163, 74, 0.88);
}

.score-fill--warning {
  background: rgba(217, 119, 6, 0.88);
}

.score-fill--danger {
  background: rgba(220, 38, 38, 0.88);
}
</style>
