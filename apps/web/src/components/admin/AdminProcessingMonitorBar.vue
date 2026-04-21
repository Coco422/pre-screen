<template>
  <Transition name="processing-banner">
    <RouterLink v-if="snapshot" class="glass-card processing-banner" :to="snapshot.detailHref">
      <div class="processing-banner__signal" aria-hidden="true">
        <span class="processing-banner__dot"></span>
      </div>

      <div class="processing-banner__body">
        <div class="processing-banner__eyebrow">系统正在处理</div>
        <div class="processing-banner__title-row">
          <strong class="processing-banner__title">{{ snapshot.taskTitle }}</strong>
          <span v-if="snapshot.activeUploadCount > 0" class="processing-banner__count">
            {{ snapshot.activeUploadCount }} 份上传
          </span>
        </div>
      </div>

      <div class="processing-banner__meta">
        <span class="processing-banner__label">{{ snapshot.label }}</span>
        <span class="processing-banner__sync">{{ syncLabel }}</span>
        <span class="processing-banner__action">查看任务</span>
      </div>
    </RouterLink>
  </Transition>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import {
  ADMIN_PROCESSING_MONITOR_STORAGE_KEY,
  formatAdminProcessingMonitorSyncLabel,
  readAdminProcessingMonitorSnapshot,
  type AdminProcessingMonitorSnapshot
} from "./adminProcessingMonitor";

const snapshot = ref<AdminProcessingMonitorSnapshot | null>(null);
const now = ref(Date.now());

let refreshTimer: number | null = null;
let clockTimer: number | null = null;

const syncLabel = computed(() => formatAdminProcessingMonitorSyncLabel(snapshot.value?.lastSyncedAt ?? null, now.value));

function refreshSnapshot() {
  snapshot.value = readAdminProcessingMonitorSnapshot();
}

function handleStorage(event: StorageEvent) {
  if (event.key === null || event.key === ADMIN_PROCESSING_MONITOR_STORAGE_KEY) {
    refreshSnapshot();
  }
}

function handleVisibilityChange() {
  if (document.visibilityState === "visible") {
    refreshSnapshot();
    now.value = Date.now();
  }
}

onMounted(() => {
  refreshSnapshot();

  refreshTimer = window.setInterval(refreshSnapshot, 2000);
  clockTimer = window.setInterval(() => {
    now.value = Date.now();
  }, 30000);

  window.addEventListener("storage", handleStorage);
  window.addEventListener("focus", refreshSnapshot);
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onBeforeUnmount(() => {
  if (refreshTimer !== null) {
    window.clearInterval(refreshTimer);
  }

  if (clockTimer !== null) {
    window.clearInterval(clockTimer);
  }

  window.removeEventListener("storage", handleStorage);
  window.removeEventListener("focus", refreshSnapshot);
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});
</script>

<style scoped>
.processing-banner {
  position: relative;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  padding: 16px 20px;
  overflow: hidden;
  border-color: rgba(15, 118, 110, 0.16);
  background:
    linear-gradient(90deg, rgba(15, 118, 110, 0.12), rgba(255, 255, 255, 0)) 0 0 / 220px 100% no-repeat,
    rgba(255, 255, 255, 0.82);
}

.processing-banner::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 10%, rgba(20, 184, 166, 0.14) 40%, transparent 70%);
  transform: translateX(-100%);
  animation: processing-banner-sweep 3.8s ease-in-out infinite;
  pointer-events: none;
}

.processing-banner__signal {
  position: relative;
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: rgba(15, 118, 110, 0.16);
  box-shadow: 0 0 0 8px rgba(15, 118, 110, 0.08);
}

.processing-banner__dot {
  position: absolute;
  inset: 2px;
  border-radius: inherit;
  background: linear-gradient(135deg, var(--accent) 0%, #2dd4bf 100%);
  animation: processing-banner-pulse 1.6s ease-in-out infinite;
}

.processing-banner__body,
.processing-banner__meta {
  position: relative;
  z-index: 1;
}

.processing-banner__body {
  min-width: 0;
}

.processing-banner__eyebrow {
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--accent-strong);
}

.processing-banner__title-row,
.processing-banner__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.processing-banner__title {
  min-width: 0;
  font-size: 1rem;
  line-height: 1.4;
  color: var(--ink-strong);
}

.processing-banner__count,
.processing-banner__sync,
.processing-banner__action {
  display: inline-flex;
  align-items: center;
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.82rem;
  font-weight: 600;
}

.processing-banner__count,
.processing-banner__sync {
  background: rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
}

.processing-banner__label {
  color: var(--ink-soft);
  font-size: 0.92rem;
  font-weight: 600;
}

.processing-banner__action {
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent-strong);
}

.processing-banner-enter-active,
.processing-banner-leave-active {
  transition: opacity 160ms ease, transform 160ms ease;
}

.processing-banner-enter-from,
.processing-banner-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@keyframes processing-banner-pulse {
  0%,
  100% {
    transform: scale(0.92);
    opacity: 0.72;
  }

  50% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes processing-banner-sweep {
  0% {
    transform: translateX(-100%);
  }

  100% {
    transform: translateX(120%);
  }
}

@media (max-width: 960px) {
  .processing-banner {
    grid-template-columns: 1fr;
    gap: 14px;
  }
}
</style>
