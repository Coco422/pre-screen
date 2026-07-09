<template>
  <section class="system-settings-page">
    <header class="page-head">
      <div>
        <h2 class="page-title">系统设置</h2>
        <p class="page-meta">管理模型连接、账号与通知偏好</p>
      </div>
    </header>

    <div class="settings-layout">
      <nav class="settings-nav" aria-label="设置分区">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="settings-nav__item"
          :class="{ 'is-active': activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <strong>{{ tab.label }}</strong>
          <span>{{ tab.hint }}</span>
        </button>
      </nav>

      <div class="settings-panel">
        <AiSettingsPanel v-if="activeTab === 'ai'" />

        <section v-else-if="activeTab === 'account'" class="placeholder-panel">
          <h3>账号与安全</h3>
          <p>规划能力：头像、显示名、登录邮箱/用户名、修改密码、会话管理。</p>
          <ul>
            <li>头像上传（本地 MinIO）</li>
            <li>修改密码（需当前密码校验）</li>
            <li>查看最近登录会话并强制下线</li>
          </ul>
          <p class="muted">后端将挂在 `auth.users` / `auth.sessions`，列入 production-cutover 后续切片。</p>
        </section>

        <section v-else class="placeholder-panel">
          <h3>消息通知</h3>
          <p>规划能力：解析完成、考卷生成完成、候选人交卷、高风险事件的站内通知与可选邮件。</p>
          <ul>
            <li>站内通知中心（替换顶栏假徽章）</li>
            <li>按事件类型开关订阅</li>
            <li>已读/未读与跳转目标页</li>
          </ul>
          <p class="muted">当前顶栏铃铛为前端占位，详见 `tasks/todos.md`。</p>
        </section>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";

import AiSettingsPanel from "./AiSettingsView.vue";

const tabs = [
  { id: "ai", label: "AI 模型", hint: "出题与解析所用模型" },
  { id: "account", label: "账号与安全", hint: "头像 / 密码（规划中）" },
  { id: "notifications", label: "消息通知", hint: "站内通知（规划中）" }
] as const;

type TabId = (typeof tabs)[number]["id"];

const route = useRoute();
const router = useRouter();
const activeTab = ref<TabId>("ai");

function tabFromQuery(value: unknown): TabId {
  if (value === "account" || value === "notifications" || value === "ai") {
    return value;
  }
  return "ai";
}

watch(
  () => route.query.tab,
  (tab) => {
    activeTab.value = tabFromQuery(tab);
  },
  { immediate: true }
);

watch(activeTab, (tab) => {
  if (route.query.tab === tab) {
    return;
  }
  void router.replace({ name: "admin-settings", query: { ...route.query, tab } });
});
</script>

<style scoped>
.system-settings-page {
  display: grid;
  gap: 18px;
}

.page-title {
  margin: 0;
}

.page-meta,
.muted {
  color: var(--ink-soft);
}

.settings-layout {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}

.settings-nav {
  display: grid;
  gap: 8px;
}

.settings-nav__item {
  display: grid;
  gap: 4px;
  text-align: left;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid #d7e1ee;
  background: #fff;
  cursor: pointer;
}

.settings-nav__item span {
  font-size: 12px;
  color: #5b6f8c;
}

.settings-nav__item.is-active {
  border-color: #3b82f6;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.25);
}

.settings-panel,
.placeholder-panel {
  min-height: 280px;
}

.placeholder-panel {
  padding: 20px;
  border: 1px solid #d7e1ee;
  border-radius: 14px;
  background: #fff;
  display: grid;
  gap: 10px;
}

.placeholder-panel ul {
  margin: 0;
  padding-left: 1.2em;
  color: #3a5070;
}

@media (max-width: 900px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }
}
</style>
