<template>
  <section class="monitor-page">
    <header class="page-head">
      <div>
        <h2 class="page-title">考试监控</h2>
        <p class="page-meta">每 10 秒刷新进行中会话 · 共 {{ sessions.length }} 场</p>
      </div>
      <button class="secondary-btn" type="button" :disabled="loading" @click="refresh">
        {{ loading ? "刷新中..." : "立即刷新" }}
      </button>
    </header>

    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <div v-if="!sessions.length && !loading" class="glass-card empty-card">当前没有进行中的考试。</div>

    <div v-else class="session-list">
      <article v-for="session in sessions" :key="session.sessionId" class="glass-card session-card">
        <div class="session-head">
          <div>
            <strong>{{ session.candidateName }}</strong>
            <div class="muted">{{ session.paperTitle }}</div>
          </div>
          <AdminToneBadge :label="session.status" tone="info" />
        </div>

        <div class="metric-row">
          <span>已答 {{ session.answeredCount }}/{{ session.totalQuestions }}</span>
          <span>风险事件 {{ session.riskEventCount }}</span>
          <span>心跳 {{ formatTime(session.lastHeartbeatAt) }}</span>
          <span>截止 {{ formatTime(session.expiresAt) }}</span>
        </div>

        <div class="session-actions">
          <button
            class="danger-btn"
            type="button"
            :disabled="forcingId === session.sessionId"
            @click="forceSubmit(session.sessionId)"
          >
            {{ forcingId === session.sessionId ? "提交中..." : "强制交卷" }}
          </button>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";

import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import { forceSubmitMonitorSession, loadMonitorSessions, type MonitorSession } from "../../lib/gateway";

const sessions = ref<MonitorSession[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const forcingId = ref("");
let timer: ReturnType<typeof setInterval> | null = null;

function formatTime(value: string | null) {
  if (!value) {
    return "—";
  }
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

async function refresh() {
  loading.value = true;
  errorMessage.value = "";
  try {
    sessions.value = await loadMonitorSessions();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

async function forceSubmit(sessionId: string) {
  forcingId.value = sessionId;
  errorMessage.value = "";
  try {
    await forceSubmitMonitorSession(sessionId);
    await refresh();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "强制交卷失败";
  } finally {
    forcingId.value = "";
  }
}

onMounted(() => {
  void refresh();
  timer = setInterval(() => {
    void refresh();
  }, 10_000);
});

onUnmounted(() => {
  if (timer) {
    clearInterval(timer);
  }
});
</script>

<style scoped>
.monitor-page {
  display: grid;
  gap: 16px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.page-title {
  margin: 0;
}

.page-meta,
.muted,
.error-message {
  color: var(--ink-soft);
}

.error-message {
  color: #8f1f2f;
}

.session-list {
  display: grid;
  gap: 12px;
}

.session-card {
  padding: 18px;
  display: grid;
  gap: 12px;
}

.session-head,
.metric-row,
.session-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.metric-row {
  justify-content: flex-start;
  color: var(--ink-soft);
  font-size: 13px;
}

.danger-btn {
  border: 1px solid rgba(176, 45, 62, 0.35);
  background: rgba(176, 45, 62, 0.08);
  color: #8f1f2f;
  border-radius: 999px;
  padding: 8px 16px;
  cursor: pointer;
}

.empty-card {
  padding: 24px;
}
</style>
