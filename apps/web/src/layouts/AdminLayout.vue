<template>
  <div class="shell-page">
    <div class="admin-shell">
      <aside class="glass-card admin-sidebar">
        <div>
          <div class="pill">HR Console</div>
          <h1 class="sidebar-title">Pre-Screen Studio</h1>
          <p class="section-copy">从简历接收到考卷发出，把初筛流程收进一条干净的工作流。</p>
        </div>
        <nav class="nav-stack">
          <RouterLink class="nav-item" to="/admin/candidates">候选人池</RouterLink>
          <RouterLink class="nav-item" to="/admin/candidates/c-001">候选人详情</RouterLink>
          <RouterLink class="nav-item" to="/admin/papers/p-001">考卷编辑</RouterLink>
        </nav>
        <div class="sidebar-footer">
          <div class="metric-tile">
            <div class="metric-value">92%</div>
            <div class="metric-label">自动流程完成度</div>
          </div>
        </div>
      </aside>

      <main class="admin-main">
        <header class="glass-card admin-header">
          <div>
            <div class="pill">Hiring Ops</div>
            <h2 class="header-title">技术岗初筛控制台</h2>
          </div>
          <button class="primary-btn">新建筛选任务</button>
        </header>

        <RouterView />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>

<style scoped>
.admin-shell {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  gap: 24px;
}

.admin-sidebar {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 24px;
}

.sidebar-title,
.header-title {
  margin: 16px 0 0;
  font-size: 1.7rem;
  letter-spacing: -0.04em;
}

.nav-stack {
  display: grid;
  gap: 10px;
  margin: 24px 0;
}

.nav-item {
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
  font-weight: 600;
}

.nav-item.router-link-active {
  color: var(--accent-strong);
  background: rgba(15, 118, 110, 0.1);
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
