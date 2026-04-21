<template>
  <div class="shell-page">
    <div class="admin-shell">
      <aside class="glass-card admin-sidebar">
        <div class="brand-block">
          <div class="pill">HR Ops</div>
          <h1 class="sidebar-title">Pre-Screen Console</h1>
          <p class="sidebar-copy">从简历初筛到发卷结果都在同一条工作链里完成。</p>
        </div>

        <nav class="nav-stack">
          <RouterLink class="nav-item" :to="{ name: 'admin-workbench' }">工作台</RouterLink>
          <RouterLink class="nav-item" :to="{ name: 'admin-task-create' }">新建任务</RouterLink>
          <RouterLink class="nav-item" :to="{ name: 'admin-candidates' }">候选人</RouterLink>
          <RouterLink class="nav-item" :to="{ name: 'admin-results' }">作答结果</RouterLink>
        </nav>

        <section class="sidebar-summary">
          <div class="summary-label">当前页面</div>
          <div class="summary-title">{{ currentTitle }}</div>
          <div class="summary-user">{{ sessionStore.userName || "HR" }} · {{ sessionStore.role || "HR" }}</div>
        </section>

        <button class="secondary-btn sidebar-signout" type="button" @click="signOut">退出登录</button>
      </aside>

      <main class="admin-main">
        <header class="glass-card admin-header">
          <div>
            <div class="pill">Hiring Ops</div>
            <h2 class="header-title">{{ currentTitle }}</h2>
          </div>
          <div class="header-actions">
            <RouterLink class="secondary-btn" :to="{ name: 'admin-workbench' }">工作台</RouterLink>
            <RouterLink class="primary-btn" :to="primaryAction.to">{{ primaryAction.label }}</RouterLink>
          </div>
        </header>

        <AdminProcessingMonitorBar />

        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterLink, RouterView, useRoute, useRouter } from "vue-router";

import AdminProcessingMonitorBar from "../components/admin/AdminProcessingMonitorBar.vue";
import { buildResultsPath, buildTaskCreatePath } from "../components/admin/adminRouting";
import { useAdminSessionStore } from "../stores/adminSession";

const route = useRoute();
const router = useRouter();
const sessionStore = useAdminSessionStore();

onMounted(async () => {
  await sessionStore.restore();
});

const currentTitle = computed(() => String(route.meta.title ?? "工作台"));

const primaryAction = computed(() => {
  switch (route.name) {
    case "admin-workbench":
      return {
        label: "新建筛选任务",
        to: buildTaskCreatePath()
      };
    case "admin-task-detail":
      return {
        label: "查看候选人",
        to: { name: "admin-candidates", query: { taskId: String(route.params.taskId ?? "") } }
      };
    case "admin-candidate-detail":
      return {
        label: "编辑画像",
        to: {
          name: "admin-candidate-edit",
          params: { candidateId: String(route.params.candidateId ?? "") }
        }
      };
    case "admin-candidate-edit":
      return {
        label: "返回详情",
        to: {
          name: "admin-candidate-detail",
          params: { candidateId: String(route.params.candidateId ?? "") }
        }
      };
    case "admin-paper-editor":
      return {
        label: "查看结果",
        to: buildResultsPath()
      };
    default:
      return {
        label: "新建筛选任务",
        to: buildTaskCreatePath()
      };
  }
});

function signOut() {
  sessionStore.signOut();
  void router.replace("/login");
}
</script>

<style scoped>
.admin-shell {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 24px;
}

.admin-sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px 20px;
}

.brand-block,
.sidebar-summary {
  display: grid;
  gap: 10px;
}

.sidebar-title,
.summary-title {
  margin: 0;
  letter-spacing: -0.04em;
}

.sidebar-title {
  font-size: 1.5rem;
}

.sidebar-copy,
.summary-label,
.summary-user {
  color: var(--ink-soft);
}

.sidebar-copy {
  margin: 0;
  line-height: 1.6;
}

.nav-stack {
  display: grid;
  gap: 10px;
}

.nav-item {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
  font-weight: 600;
}

.nav-item.router-link-active {
  color: var(--accent-strong);
  background: rgba(15, 118, 110, 0.1);
}

.summary-label {
  font-size: 0.82rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.summary-user {
  font-size: 0.95rem;
}

.sidebar-signout {
  margin-top: auto;
}

.admin-main {
  display: grid;
  gap: 24px;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
}

.header-title {
  margin: 14px 0 0;
  font-size: 1.7rem;
  letter-spacing: -0.04em;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 960px) {
  .admin-shell {
    grid-template-columns: 1fr;
  }

  .admin-header {
    align-items: flex-start;
    flex-direction: column;
    gap: 16px;
  }
}
</style>
