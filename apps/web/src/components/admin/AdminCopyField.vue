<template>
  <div class="copy-field">
    <div class="copy-label">{{ label }}</div>
    <div class="copy-value">{{ value || placeholder }}</div>
    <button class="secondary-btn copy-button" type="button" :disabled="!value" @click="copyValue">
      {{ copied ? "已复制" : buttonLabel }}
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const props = withDefaults(
  defineProps<{
    label: string;
    value: string;
    buttonLabel?: string;
    placeholder?: string;
  }>(),
  {
    buttonLabel: "复制",
    placeholder: "尚未生成"
  }
);

const copied = ref(false);

async function copyValue() {
  if (!props.value) {
    return;
  }

  try {
    await navigator.clipboard.writeText(props.value);
  } catch {
    const textarea = document.createElement("textarea");
    textarea.value = props.value;
    textarea.setAttribute("readonly", "true");
    textarea.style.position = "absolute";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
  }

  copied.value = true;
  window.setTimeout(() => {
    copied.value = false;
  }, 1600);
}
</script>

<style scoped>
.copy-field {
  display: grid;
  gap: 8px;
}

.copy-label {
  color: var(--ink-soft);
  font-size: 0.88rem;
}

.copy-value {
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(20, 33, 61, 0.04);
  border: 1px solid rgba(20, 33, 61, 0.06);
  word-break: break-all;
}

.copy-button {
  justify-self: start;
}
</style>
