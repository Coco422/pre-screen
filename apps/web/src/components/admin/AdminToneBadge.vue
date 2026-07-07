<template>
  <span class="tone-badge" :class="`tone-badge--${tone}`">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string;
    tone?: "neutral" | "info" | "success" | "warning" | "danger";
  }>(),
  {
    tone: "neutral"
  }
);
</script>

<style scoped>
.tone-badge {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  border: 1px solid transparent;
  font-size: 0.84rem;
  font-weight: 700;
}

.tone-badge--neutral {
  background: rgba(20, 33, 61, 0.06);
  border-color: rgba(20, 33, 61, 0.08);
  color: var(--ink-soft);
}

.tone-badge--info {
  background: rgba(14, 116, 144, 0.12);
  border-color: rgba(14, 116, 144, 0.16);
  color: #0f5f78;
}

.tone-badge--success {
  background: rgba(21, 128, 61, 0.12);
  border-color: rgba(21, 128, 61, 0.16);
  color: #166534;
}

.tone-badge--warning {
  background: rgba(217, 119, 6, 0.12);
  border-color: rgba(217, 119, 6, 0.16);
  color: #b45309;
}

.tone-badge--danger {
  background: rgba(220, 38, 38, 0.12);
  border-color: rgba(220, 38, 38, 0.16);
  color: #b91c1c;
}
</style>
