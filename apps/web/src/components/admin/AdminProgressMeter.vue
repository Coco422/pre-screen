<template>
  <div class="meter">
    <div class="meter-top">
      <div class="meter-title">{{ label }}</div>
      <div class="meter-value">{{ safeValue }}%</div>
    </div>
    <div class="meter-track">
      <div class="meter-fill" :class="`meter-fill--${tone}`" :style="{ width: `${safeValue}%` }"></div>
    </div>
    <div v-if="caption" class="meter-caption">{{ caption }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = withDefaults(
  defineProps<{
    label: string;
    value: number;
    caption?: string;
    tone?: "neutral" | "info" | "success" | "warning" | "danger";
  }>(),
  {
    caption: "",
    tone: "neutral"
  }
);

const safeValue = computed(() => Math.min(100, Math.max(0, Math.round(props.value))));
</script>

<style scoped>
.meter {
  display: grid;
  gap: 8px;
}

.meter-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.meter-title,
.meter-caption {
  color: var(--ink-soft);
}

.meter-title {
  font-size: 0.92rem;
}

.meter-value {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--ink-base);
}

.meter-track {
  overflow: hidden;
  height: 10px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.08);
}

.meter-fill {
  height: 100%;
  border-radius: inherit;
  transition: width 180ms ease;
}

.meter-fill--neutral {
  background: linear-gradient(90deg, rgba(71, 85, 105, 0.72), rgba(100, 116, 139, 0.96));
}

.meter-fill--info {
  background: linear-gradient(90deg, rgba(14, 116, 144, 0.72), rgba(6, 182, 212, 0.96));
}

.meter-fill--success {
  background: linear-gradient(90deg, rgba(21, 128, 61, 0.72), rgba(34, 197, 94, 0.96));
}

.meter-fill--warning {
  background: linear-gradient(90deg, rgba(217, 119, 6, 0.72), rgba(251, 191, 36, 0.96));
}

.meter-fill--danger {
  background: linear-gradient(90deg, rgba(220, 38, 38, 0.72), rgba(248, 113, 113, 0.96));
}

.meter-caption {
  font-size: 0.84rem;
  line-height: 1.5;
}
</style>
