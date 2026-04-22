# Pre-Screen UI Redesign Phase One Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Phase One Pre-Screen web UI around the approved redesign spec by introducing the new route skeleton, Element Plus-based design foundation, and three high-fidelity sample pages: HR login, admin dashboard, and candidate list.

**Architecture:** Keep the existing `apps/web` Vue app, but reorganize it into a clearer `Admin Console` and `Exam Workspace` route structure. Reuse existing data-loading APIs from `src/lib/gateway.ts`, rebuild the admin shell and sample pages with Element Plus, and add placeholder pages for routes that are part of the approved information architecture but not yet fully implemented.

**Tech Stack:** Vue 3, TypeScript, Vue Router, Pinia, Element Plus, Vitest, Vue Test Utils, Vite.

---

## File Structure

- `apps/web/package.json`
  Add the UI and test dependencies needed for the redesign.
- `apps/web/src/main.ts`
  Register Element Plus and its base stylesheet.
- `apps/web/src/router/index.ts`
  Move the app onto the approved route skeleton for `/admin/*` and `/exam/*`.
- `apps/web/src/router/router.spec.ts`
  Verify the new route structure.
- `apps/web/src/styles.css`
  Define the new global design tokens, surfaces, layout helpers, and shared UI rules.
- `apps/web/src/components/layout/adminNavigation.ts`
  Store the left-nav structure in one place so routing and layout stay aligned.
- `apps/web/src/components/layout/adminNavigation.spec.ts`
  Verify the nav structure matches the approved information architecture.
- `apps/web/src/components/layout/AdminSidebarNav.vue`
  Render the left admin navigation.
- `apps/web/src/components/layout/AdminTopbar.vue`
  Render the top global bar.
- `apps/web/src/layouts/AdminLayout.vue`
  Replace the current shell with the redesigned admin console layout.
- `apps/web/src/views/shared/PlaceholderView.vue`
  Reusable placeholder view for routes approved in the architecture but not yet implemented.
- `apps/web/src/views/admin/AdminLoginView.vue`
  Rebuild the login page around the approved high-fidelity layout.
- `apps/web/src/views/admin/AdminLoginView.spec.ts`
  Verify the login page renders the HR-only layout and CTA correctly.
- `apps/web/src/views/admin/AdminDashboardView.vue`
  Dashboard view for `/admin/dashboard`; starts as a stub during routing work, then becomes the full Phase One dashboard.
- `apps/web/src/views/admin/AdminDashboardView.spec.ts`
  Verify the dashboard renders metrics and the three primary content regions.
- `apps/web/src/views/admin/CandidateListView.vue`
  Rebuild the candidate list into a filter + table page using Element Plus.
- `apps/web/src/views/admin/CandidateListView.spec.ts`
  Verify the candidate list renders filters, table columns, and status-driven actions.
- `apps/web/src/views/exam/ExamStartView.vue`
  Placeholder exam start page aligned to the new route structure.
- `apps/web/src/views/exam/ExamSessionView.vue`
  Placeholder exam session page aligned to the new route structure.
- `apps/web/src/views/exam/ExamSubmittedView.vue`
  Placeholder exam submitted page aligned to the new route structure.

## Assumptions

- Phase One is intentionally scoped to the design foundation plus three sample pages, not the entire web app.
- Existing API functions from `src/lib/gateway.ts` stay in place for now; the work is primarily a UI and route reorganization.
- Admin surfaces should use Element Plus components wherever the library already solves the interaction well.
- The login page may use a custom SVG or generated image asset later, but the initial implementation can ship with a code-native visual panel so that the structure is stable before image iteration.

## Task 1: Install the Redesign Dependencies and Lock the New Route Skeleton

**Files:**
- Modify: `apps/web/package.json`
- Modify: `apps/web/src/main.ts`
- Modify: `apps/web/src/router/index.ts`
- Modify: `apps/web/src/router/router.spec.ts`
- Create: `apps/web/src/views/shared/PlaceholderView.vue`
- Create: `apps/web/src/views/admin/AdminDashboardView.vue`
- Create: `apps/web/src/views/exam/ExamStartView.vue`
- Create: `apps/web/src/views/exam/ExamSessionView.vue`
- Create: `apps/web/src/views/exam/ExamSubmittedView.vue`
- Test: `apps/web/src/router/router.spec.ts`

- [ ] **Step 1: Write the failing route-structure test**

```ts
// apps/web/src/router/router.spec.ts
import { describe, expect, it } from "vitest";

import { routes } from "./index";

describe("router", () => {
  it("redirects the root route to login", () => {
    const rootRoute = routes.find((route) => route.path === "/");

    expect(rootRoute?.redirect).toBe("/login");
  });

  it("includes the admin dashboard route", () => {
    expect(routes.some((route) => route.path === "/admin")).toBe(true);
    const adminRoute = routes.find((route) => route.path === "/admin");

    const childPaths = Array.isArray(adminRoute?.children) ? adminRoute.children.map((route) => route.path) : [];

    expect(childPaths).toContain("dashboard");
    expect(childPaths).toContain("tasks");
    expect(childPaths).toContain("candidates");
    expect(childPaths).toContain("papers");
    expect(childPaths).toContain("results");
    expect(childPaths).toContain("risk");
    expect(childPaths).toContain("settings");
  });

  it("includes the exam route trilogy", () => {
    expect(routes.some((route) => route.path === "/exam/:token/start")).toBe(true);
    expect(routes.some((route) => route.path === "/exam/:token/session")).toBe(true);
    expect(routes.some((route) => route.path === "/exam/:token/submitted")).toBe(true);
  });
});
```

- [ ] **Step 2: Run the route test to verify it fails**

Run: `npm --prefix apps/web run test -- src/router/router.spec.ts`

Expected: FAIL because the current router still uses `/admin` as the workbench child root and does not expose the new `/admin/dashboard` and `/exam/:token/*` structure.

- [ ] **Step 3: Add Element Plus, Vue Test Utils, and the new route skeleton**

```json
// apps/web/package.json
{
  "name": "pre-screen-web",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc --noEmit && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "@element-plus/icons-vue": "^2.3.1",
    "element-plus": "^2.11.5",
    "pinia": "^3.0.4",
    "vue": "^3.5.13",
    "vue-router": "^4.5.1"
  },
  "devDependencies": {
    "@types/node": "^24.7.2",
    "@vitejs/plugin-vue": "^6.0.1",
    "@vue/test-utils": "^2.4.6",
    "jsdom": "^26.1.0",
    "typescript": "^5.9.3",
    "vite": "^7.1.9",
    "vitest": "^3.2.4",
    "vue-tsc": "^3.1.0"
  }
}
```

```ts
// apps/web/src/main.ts
import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";

import App from "./App.vue";
import { router } from "./router";
import "./styles.css";

const app = createApp(App);

app.use(createPinia());
app.use(router);
app.use(ElementPlus);
app.mount("#app");
```

```vue
<!-- apps/web/src/views/admin/AdminDashboardView.vue -->
<template>
  <section class="page-panel">工作台将在 Phase One Task 4 中完成重构。</section>
</template>
```

```vue
<!-- apps/web/src/views/shared/PlaceholderView.vue -->
<template>
  <section class="placeholder-page">
    <el-empty :description="description">
      <template #image>
        <div class="placeholder-mark">{{ iconLabel }}</div>
      </template>
      <el-button v-if="actionLabel" type="primary" @click="$emit('action')">{{ actionLabel }}</el-button>
    </el-empty>
  </section>
</template>

<script setup lang="ts">
defineProps<{
  description: string;
  iconLabel?: string;
  actionLabel?: string;
}>();

defineEmits<{
  action: [];
}>();
</script>
```

```vue
<!-- apps/web/src/views/exam/ExamStartView.vue -->
<template>
  <PlaceholderView description="考试验证页将在后续阶段重构。" icon-label="Start" />
</template>

<script setup lang="ts">
import PlaceholderView from "../shared/PlaceholderView.vue";
</script>
```

```vue
<!-- apps/web/src/views/exam/ExamSessionView.vue -->
<template>
  <PlaceholderView description="在线作答页将在后续阶段重构。" icon-label="Exam" />
</template>

<script setup lang="ts">
import PlaceholderView from "../shared/PlaceholderView.vue";
</script>
```

```vue
<!-- apps/web/src/views/exam/ExamSubmittedView.vue -->
<template>
  <PlaceholderView description="提交完成页将在后续阶段重构。" icon-label="Done" />
</template>

<script setup lang="ts">
import PlaceholderView from "../shared/PlaceholderView.vue";
</script>
```

```ts
// apps/web/src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import AdminLayout from "../layouts/AdminLayout.vue";
import { hasAdminSession } from "../stores/adminSession";

export const routes: RouteRecordRaw[] = [
  {
    path: "/",
    redirect: "/login"
  },
  {
    path: "/login",
    name: "admin-login",
    meta: { title: "HR 登录" },
    component: () => import("../views/admin/AdminLoginView.vue")
  },
  {
    path: "/admin",
    component: AdminLayout,
    children: [
      {
        path: "",
        redirect: "/admin/dashboard"
      },
      {
        path: "dashboard",
        name: "admin-dashboard",
        meta: { title: "工作台" },
        component: () => import("../views/admin/AdminDashboardView.vue")
      },
      {
        path: "tasks",
        name: "admin-tasks",
        meta: { title: "任务中心" },
        component: () => import("../views/shared/PlaceholderView.vue"),
        props: { description: "任务中心将在后续阶段重构。", iconLabel: "Tasks" }
      },
      {
        path: "papers",
        name: "admin-papers",
        meta: { title: "考卷管理" },
        component: () => import("../views/shared/PlaceholderView.vue"),
        props: { description: "考卷管理列表将在后续阶段重构。", iconLabel: "Papers" }
      },
      {
        path: "tasks/new",
        name: "admin-task-create",
        meta: { title: "新建筛选任务" },
        component: () => import("../views/admin/TaskCreateView.vue")
      },
      {
        path: "tasks/:taskId",
        name: "admin-task-detail",
        meta: { title: "任务详情" },
        component: () => import("../views/admin/TaskDetailView.vue")
      },
      {
        path: "candidates",
        name: "admin-candidates",
        meta: { title: "候选人" },
        component: () => import("../views/admin/CandidateListView.vue")
      },
      {
        path: "candidates/:candidateId",
        name: "admin-candidate-detail",
        meta: { title: "候选人详情" },
        component: () => import("../views/admin/CandidateDetailView.vue")
      },
      {
        path: "candidates/:candidateId/edit",
        name: "admin-candidate-edit",
        meta: { title: "编辑画像" },
        component: () => import("../views/admin/CandidateEditView.vue")
      },
      {
        path: "papers/:paperId",
        name: "admin-paper-editor",
        meta: { title: "考卷管理" },
        component: () => import("../views/admin/PaperEditorView.vue")
      },
      {
        path: "results",
        name: "admin-results",
        meta: { title: "结果中心" },
        component: () => import("../views/admin/ResultListView.vue")
      },
      {
        path: "results/:resultId",
        name: "admin-result-detail",
        meta: { title: "结果详情" },
        component: () => import("../views/admin/ResultDetailView.vue")
      },
      {
        path: "risk",
        name: "admin-risk",
        meta: { title: "风险管理" },
        component: () => import("../views/shared/PlaceholderView.vue"),
        props: { description: "风险管理将在后续阶段重构。", iconLabel: "Risk" }
      },
      {
        path: "settings",
        name: "admin-settings",
        meta: { title: "系统设置" },
        component: () => import("../views/shared/PlaceholderView.vue"),
        props: { description: "系统设置将在后续阶段重构。", iconLabel: "Settings" }
      }
    ]
  },
  {
    path: "/exam/:token/start",
    name: "exam-start",
    component: () => import("../views/exam/ExamStartView.vue")
  },
  {
    path: "/exam/:token/session",
    name: "exam-session",
    component: () => import("../views/exam/ExamSessionView.vue")
  },
  {
    path: "/exam/:token/submitted",
    name: "exam-submitted",
    component: () => import("../views/exam/ExamSubmittedView.vue")
  }
];

export const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to) => {
  const needsAdminSession = to.path.startsWith("/admin");
  const loggedIn = hasAdminSession();

  if (needsAdminSession && !loggedIn) {
    return "/login";
  }

  if (to.path === "/login" && loggedIn) {
    return "/admin/dashboard";
  }

  return true;
});
```

- [ ] **Step 4: Run the route test to verify it passes**

Run: `npm --prefix apps/web run test -- src/router/router.spec.ts`

Expected: PASS with 3 passing tests.

- [ ] **Step 5: Commit the routing foundation**

```bash
git add apps/web/package.json apps/web/src/main.ts apps/web/src/router/index.ts apps/web/src/router/router.spec.ts apps/web/src/views/shared/PlaceholderView.vue apps/web/src/views/admin/AdminDashboardView.vue apps/web/src/views/exam/ExamStartView.vue apps/web/src/views/exam/ExamSessionView.vue apps/web/src/views/exam/ExamSubmittedView.vue
git commit -m "feat: add phase-one route skeleton"
```

## Task 2: Build the Global Admin Shell and Design Tokens

**Files:**
- Modify: `apps/web/src/styles.css`
- Create: `apps/web/src/components/layout/adminNavigation.ts`
- Create: `apps/web/src/components/layout/adminNavigation.spec.ts`
- Create: `apps/web/src/components/layout/AdminSidebarNav.vue`
- Create: `apps/web/src/components/layout/AdminTopbar.vue`
- Modify: `apps/web/src/layouts/AdminLayout.vue`
- Test: `apps/web/src/components/layout/adminNavigation.spec.ts`

- [ ] **Step 1: Write the failing navigation-structure test**

```ts
// apps/web/src/components/layout/adminNavigation.spec.ts
import { describe, expect, it } from "vitest";

import { adminNavigation } from "./adminNavigation";

describe("adminNavigation", () => {
  it("defines the approved primary navigation", () => {
    expect(adminNavigation.map((item) => item.label)).toEqual([
      "工作台",
      "任务中心",
      "候选人",
      "考卷管理",
      "结果中心",
      "风险管理",
      "系统设置"
    ]);
  });

  it("marks the placeholder destinations that are not implemented in phase one", () => {
    const placeholderItems = adminNavigation.filter((item) => item.placeholder);

    expect(placeholderItems.map((item) => item.label)).toEqual(["任务中心", "考卷管理", "风险管理", "系统设置"]);
  });
});
```

- [ ] **Step 2: Run the navigation test to verify it fails**

Run: `npm --prefix apps/web run test -- src/components/layout/adminNavigation.spec.ts`

Expected: FAIL because `adminNavigation.ts` does not exist yet.

- [ ] **Step 3: Add the nav config, shell components, and global tokens**

```ts
// apps/web/src/components/layout/adminNavigation.ts
export type AdminNavigationItem = {
  label: string;
  icon: string;
  to: { name: string };
  placeholder?: boolean;
};

export const adminNavigation: AdminNavigationItem[] = [
  { label: "工作台", icon: "HomeFilled", to: { name: "admin-dashboard" } },
  { label: "任务中心", icon: "Tickets", to: { name: "admin-tasks" }, placeholder: true },
  { label: "候选人", icon: "UserFilled", to: { name: "admin-candidates" } },
  { label: "考卷管理", icon: "Document", to: { name: "admin-papers" }, placeholder: true },
  { label: "结果中心", icon: "DataAnalysis", to: { name: "admin-results" } },
  { label: "风险管理", icon: "WarningFilled", to: { name: "admin-risk" }, placeholder: true },
  { label: "系统设置", icon: "Setting", to: { name: "admin-settings" }, placeholder: true }
];
```

```vue
<!-- apps/web/src/components/layout/AdminSidebarNav.vue -->
<template>
  <aside class="admin-sidebar">
    <div class="admin-sidebar__brand">
      <div class="admin-sidebar__logo">P</div>
      <div>
        <strong>Pre-Screen</strong>
        <p>招聘预筛控制台</p>
      </div>
    </div>

    <nav class="admin-sidebar__nav">
      <RouterLink
        v-for="item in adminNavigation"
        :key="item.label"
        class="admin-sidebar__item"
        :class="{ 'is-placeholder': item.placeholder }"
        :to="item.to"
      >
        <span>{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";

import { adminNavigation } from "./adminNavigation";
</script>
```

```vue
<!-- apps/web/src/components/layout/AdminTopbar.vue -->
<template>
  <header class="admin-topbar">
    <div>
      <p class="admin-topbar__eyebrow">Pre-Screen Console</p>
      <h1>{{ title }}</h1>
    </div>

    <div class="admin-topbar__actions">
      <el-badge :value="1" class="admin-topbar__badge">
        <el-button circle>
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>
      <div class="admin-topbar__user">{{ userName }}</div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Bell } from "@element-plus/icons-vue";

defineProps<{
  title: string;
  userName: string;
}>();
</script>
```

```vue
<!-- apps/web/src/layouts/AdminLayout.vue -->
<template>
  <div class="admin-console">
    <AdminSidebarNav />

    <main class="admin-console__main">
      <AdminTopbar :title="currentTitle" :user-name="sessionStore.userName || 'HR_Admin'" />
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterView, useRoute } from "vue-router";

import AdminSidebarNav from "../components/layout/AdminSidebarNav.vue";
import AdminTopbar from "../components/layout/AdminTopbar.vue";
import { useAdminSessionStore } from "../stores/adminSession";

const route = useRoute();
const sessionStore = useAdminSessionStore();

onMounted(async () => {
  await sessionStore.restore();
});

const currentTitle = computed(() => String(route.meta.title ?? "工作台"));
</script>
```

```css
/* apps/web/src/styles.css */
:root {
  font-family: "PingFang SC", "Inter", "Segoe UI", sans-serif;
  color: #1f2a44;
  background: linear-gradient(180deg, #f3f8ff 0%, #edf4ff 100%);
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  --bg-page: #f4f8ff;
  --bg-panel: rgba(255, 255, 255, 0.92);
  --bg-panel-strong: #ffffff;
  --bg-soft: #edf5ff;
  --line-soft: rgba(76, 111, 163, 0.16);
  --line-strong: rgba(54, 92, 150, 0.24);
  --text-primary: #1d2a44;
  --text-secondary: #6d7b95;
  --brand-500: #2f6bff;
  --brand-600: #2458d6;
  --brand-050: #edf4ff;
  --success: #1fb26b;
  --warning: #ff9f0a;
  --danger: #f05252;
  --radius-xl: 24px;
  --radius-lg: 18px;
  --radius-md: 14px;
  --shadow-panel: 0 20px 50px rgba(33, 74, 140, 0.08);
}

* {
  box-sizing: border-box;
}

html,
body,
#app {
  min-height: 100%;
  margin: 0;
}

body {
  color: var(--text-primary);
  background:
    radial-gradient(circle at top left, rgba(47, 107, 255, 0.12), transparent 28%),
    linear-gradient(180deg, #f8fbff 0%, #edf4ff 100%);
}

a {
  color: inherit;
  text-decoration: none;
}

.admin-console {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 20px;
  min-height: 100vh;
  padding: 20px;
}

.admin-console__main {
  display: grid;
  gap: 20px;
}

.admin-sidebar,
.admin-topbar,
.page-panel {
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  background: var(--bg-panel);
  box-shadow: var(--shadow-panel);
}

.admin-sidebar {
  display: grid;
  align-content: start;
  gap: 24px;
  padding: 22px 18px;
}

.admin-sidebar__brand {
  display: flex;
  gap: 12px;
  align-items: center;
}

.admin-sidebar__logo {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #2f6bff 0%, #6aa8ff 100%);
  color: #fff;
  font-weight: 700;
}

.admin-sidebar__brand p {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.admin-sidebar__nav {
  display: grid;
  gap: 8px;
}

.admin-sidebar__item {
  padding: 11px 14px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-weight: 600;
}

.admin-sidebar__item.router-link-active {
  color: var(--brand-600);
  background: var(--brand-050);
}

.admin-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 22px 24px;
}

.admin-topbar__eyebrow {
  margin: 0 0 8px;
  color: var(--brand-600);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.admin-topbar h1 {
  margin: 0;
  font-size: 30px;
}

.admin-topbar__actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.admin-topbar__user {
  padding: 10px 14px;
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  background: #fff;
  font-weight: 600;
}

.page-panel {
  padding: 24px;
}

.placeholder-page {
  display: grid;
  place-items: center;
  min-height: 480px;
}

.placeholder-mark {
  display: grid;
  place-items: center;
  width: 72px;
  height: 72px;
  border-radius: 24px;
  background: linear-gradient(135deg, #2f6bff 0%, #8ab6ff 100%);
  color: #fff;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .admin-console {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 4: Run the navigation test to verify it passes**

Run: `npm --prefix apps/web run test -- src/components/layout/adminNavigation.spec.ts`

Expected: PASS with 2 passing tests.

- [ ] **Step 5: Commit the admin shell foundation**

```bash
git add apps/web/src/styles.css apps/web/src/components/layout/adminNavigation.ts apps/web/src/components/layout/adminNavigation.spec.ts apps/web/src/components/layout/AdminSidebarNav.vue apps/web/src/components/layout/AdminTopbar.vue apps/web/src/layouts/AdminLayout.vue
git commit -m "feat: add admin shell foundation"
```

## Task 3: Rebuild the HR Login Page

**Files:**
- Modify: `apps/web/src/views/admin/AdminLoginView.vue`
- Create: `apps/web/src/views/admin/AdminLoginView.spec.ts`
- Test: `apps/web/src/views/admin/AdminLoginView.spec.ts`

- [ ] **Step 1: Write the failing login-page rendering test**

```ts
// apps/web/src/views/admin/AdminLoginView.spec.ts
import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";

import AdminLoginView from "./AdminLoginView.vue";

vi.mock("vue-router", () => ({
  useRouter: () => ({
    replace: vi.fn()
  })
}));

vi.mock("../../stores/adminSession", () => ({
  useAdminSessionStore: () => ({
    signIn: vi.fn(async () => ({ sessionToken: "token" }))
  })
}));

describe("AdminLoginView", () => {
  it("renders the HR-only login layout from the approved design direction", () => {
    const wrapper = mount(AdminLoginView, {
      global: {
        stubs: {
          ElInput: true,
          ElCheckbox: true,
          ElAlert: true,
          ElButton: { template: "<button type='submit'><slot /></button>" }
        }
      }
    });

    expect(wrapper.text()).toContain("Pre-Screen");
    expect(wrapper.text()).toContain("HR 登录");
    expect(wrapper.text()).toContain("技术招聘智能筛选系统");
    expect(wrapper.text()).not.toContain("候选人登录");
    expect(wrapper.find('button[type="submit"]').text()).toContain("登录");
  });
});
```

- [ ] **Step 2: Run the login test to verify it fails**

Run: `npm --prefix apps/web run test -- src/views/admin/AdminLoginView.spec.ts`

Expected: FAIL because the current login page still renders the narrative-heavy split layout and does not match the approved HR-only copy.

- [ ] **Step 3: Replace the login page with the approved split layout**

```vue
<!-- apps/web/src/views/admin/AdminLoginView.vue -->
<template>
  <div class="login-screen">
    <section class="login-screen__brand">
      <div class="login-screen__copy">
        <h1>Pre-Screen</h1>
        <p>技术招聘智能筛选系统</p>
      </div>

      <div class="login-hero">
        <div class="login-hero__grid"></div>
        <div class="login-hero__shield">
          <span></span>
        </div>
      </div>
    </section>

    <section class="login-card">
      <header class="login-card__header">
        <h2>HR 登录</h2>
        <p>进入招聘预筛控制台</p>
      </header>

      <form class="login-form" @submit.prevent="submit">
        <label>
          <span>账号</span>
          <el-input v-model="username" placeholder="请输入账号" :disabled="submitting" />
        </label>

        <label>
          <span>密码</span>
          <el-input v-model="password" type="password" show-password placeholder="请输入密码" :disabled="submitting" />
        </label>

        <div class="login-form__meta">
          <el-checkbox v-model="rememberMe">记住账号</el-checkbox>
          <button type="button">忘记密码?</button>
        </div>

        <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />

        <el-button class="login-form__submit" type="primary" native-type="submit" :loading="submitting">
          登录
        </el-button>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { useAdminSessionStore } from "../../stores/adminSession";

const router = useRouter();
const sessionStore = useAdminSessionStore();
const username = ref("hr-demo");
const password = ref("demo-pass");
const rememberMe = ref(true);
const submitting = ref(false);
const errorMessage = ref("");

async function submit() {
  submitting.value = true;
  errorMessage.value = "";

  try {
    await sessionStore.signIn(username.value.trim(), password.value.trim());
    await router.replace("/admin/dashboard");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
}
</script>
```

```css
/* append to apps/web/src/styles.css */
.login-screen {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(380px, 440px);
  gap: 24px;
  min-height: 100vh;
  padding: 28px;
}

.login-screen__brand,
.login-card {
  border: 1px solid var(--line-soft);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-panel);
}

.login-screen__brand {
  position: relative;
  overflow: hidden;
  padding: 42px;
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.96) 0%, rgba(238, 246, 255, 0.98) 100%);
}

.login-screen__copy h1 {
  margin: 0;
  font-size: 52px;
  letter-spacing: -0.04em;
}

.login-screen__copy p {
  margin: 12px 0 0;
  color: var(--text-secondary);
  font-size: 20px;
}

.login-hero {
  position: relative;
  min-height: 420px;
  margin-top: 28px;
}

.login-hero__grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(47, 107, 255, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(47, 107, 255, 0.08) 1px, transparent 1px);
  background-size: 42px 42px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.9), transparent);
}

.login-hero__shield {
  position: absolute;
  left: 10%;
  bottom: 4%;
  display: grid;
  place-items: center;
  width: 240px;
  height: 240px;
  border-radius: 32px;
  background: radial-gradient(circle at top, rgba(255, 255, 255, 0.85), rgba(102, 163, 255, 0.8));
  box-shadow: 0 32px 60px rgba(47, 107, 255, 0.22);
}

.login-hero__shield span {
  width: 88px;
  height: 104px;
  background: linear-gradient(180deg, #2f6bff 0%, #84b4ff 100%);
  clip-path: polygon(50% 0%, 90% 18%, 90% 56%, 50% 100%, 10% 56%, 10% 18%);
}

.login-card {
  display: grid;
  align-content: center;
  padding: 36px 32px;
}

.login-card__header h2 {
  margin: 0;
  font-size: 30px;
}

.login-card__header p {
  margin: 10px 0 0;
  color: var(--text-secondary);
}

.login-form {
  display: grid;
  gap: 18px;
  margin-top: 28px;
}

.login-form label {
  display: grid;
  gap: 8px;
  font-weight: 600;
}

.login-form__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--text-secondary);
}

.login-form__meta button {
  border: 0;
  background: transparent;
  color: var(--brand-600);
  cursor: pointer;
}

.login-form__submit {
  width: 100%;
}
```

- [ ] **Step 4: Run the login test to verify it passes**

Run: `npm --prefix apps/web run test -- src/views/admin/AdminLoginView.spec.ts`

Expected: PASS with 1 passing test.

- [ ] **Step 5: Commit the login redesign**

```bash
git add apps/web/src/views/admin/AdminLoginView.vue apps/web/src/views/admin/AdminLoginView.spec.ts apps/web/src/styles.css
git commit -m "feat: redesign hr login page"
```

## Task 4: Rebuild the Admin Dashboard

**Files:**
- Modify: `apps/web/src/views/admin/AdminDashboardView.vue`
- Create: `apps/web/src/views/admin/AdminDashboardView.spec.ts`
- Test: `apps/web/src/views/admin/AdminDashboardView.spec.ts`

- [ ] **Step 1: Write the failing dashboard rendering test**

```ts
// apps/web/src/views/admin/AdminDashboardView.spec.ts
import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import AdminDashboardView from "./AdminDashboardView.vue";

vi.mock("../../lib/gateway", () => ({
  loadTasks: vi.fn(async () => [
    { id: "task-1", title: "后端工程师筛选", role: "后端工程师", status: "进行中", candidateCount: 36, uploadCount: 40, createdAt: "2026-04-22T09:00:00Z" }
  ]),
  loadCandidates: vi.fn(async () => [
    { id: "c-1", taskId: "task-1", name: "张三", role: "后端工程师", city: "上海", status: "待审核", quality: "高", summary: "5 年后端经验", skills: ["Java"], paperId: "paper-1" }
  ]),
  loadResults: vi.fn(async () => [
    { resultId: "r-1", candidateId: "c-1", candidateName: "张三", role: "后端工程师", submittedAt: "2026-04-22T10:00:00Z", totalScore: 85, status: "已交卷" }
  ])
}));

describe("AdminDashboardView", () => {
  it("renders the phase-one dashboard metrics and primary regions", async () => {
    const wrapper = mount(AdminDashboardView, {
      global: {
        stubs: {
          RouterLink: { template: "<a><slot /></a>" },
          ElTable: { props: ["data"], template: "<div><slot />{{ JSON.stringify(data) }}</div>" },
          ElTableColumn: { template: "<div><slot /></div>" }
        }
      }
    });

    await flushPromises();

    expect(wrapper.text()).toContain("待处理候选人");
    expect(wrapper.text()).toContain("最近任务");
    expect(wrapper.text()).toContain("最新结果");
    expect(wrapper.text()).toContain("异常事件");
    expect(wrapper.text()).toContain("张三");
  });
});
```

- [ ] **Step 2: Run the dashboard test to verify it fails**

Run: `npm --prefix apps/web run test -- src/views/admin/AdminDashboardView.spec.ts`

Expected: FAIL because the dashboard stub from Task 1 does not render the approved metrics and primary regions.

- [ ] **Step 3: Implement the new dashboard**

```vue
<!-- apps/web/src/views/admin/AdminDashboardView.vue -->
<template>
  <section class="dashboard-page">
    <div class="dashboard-metrics">
      <article v-for="metric in metrics" :key="metric.label" class="dashboard-metric">
        <p>{{ metric.label }}</p>
        <strong>{{ metric.value }}</strong>
      </article>
    </div>

    <div class="dashboard-columns">
      <section class="page-panel">
        <div class="section-head">
          <div>
            <h2>待处理候选人</h2>
            <p>优先展示最需要推进的候选人。</p>
          </div>
          <RouterLink :to="{ name: 'admin-candidates' }">查看全部</RouterLink>
        </div>

        <el-table :data="priorityCandidates" stripe>
          <el-table-column prop="name" label="姓名" />
          <el-table-column prop="role" label="岗位" />
          <el-table-column prop="status" label="状态" />
        </el-table>
      </section>

      <section class="page-panel">
        <div class="section-head">
          <div>
            <h2>最近任务</h2>
            <p>按岗位维度查看筛选推进情况。</p>
          </div>
          <RouterLink :to="{ name: 'admin-tasks' }">进入</RouterLink>
        </div>

        <el-table :data="tasks" stripe>
          <el-table-column prop="title" label="任务名称" />
          <el-table-column prop="role" label="岗位" />
          <el-table-column prop="status" label="状态" />
        </el-table>
      </section>

      <section class="page-panel">
        <div class="section-head">
          <div>
            <h2>最新结果</h2>
            <p>最近完成作答的候选人结果。</p>
          </div>
          <RouterLink :to="{ name: 'admin-results' }">结果中心</RouterLink>
        </div>

        <el-table :data="results" stripe>
          <el-table-column prop="candidateName" label="姓名" />
          <el-table-column prop="role" label="岗位" />
          <el-table-column prop="totalScore" label="总分" />
        </el-table>
      </section>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { loadCandidates, loadResults, loadTasks, type CandidateCard, type ResultSummary, type ScreeningTaskSummary } from "../../lib/gateway";

const tasks = ref<ScreeningTaskSummary[]>([]);
const candidates = ref<CandidateCard[]>([]);
const results = ref<ResultSummary[]>([]);

const priorityCandidates = computed(() => candidates.value.slice(0, 5));
const metrics = computed(() => [
  { label: "待处理候选人", value: String(candidates.value.length) },
  { label: "待发卷人数", value: String(candidates.value.filter((item) => item.status === "待发卷").length) },
  { label: "进行中考试", value: String(candidates.value.filter((item) => item.status === "已开考").length) },
  { label: "已完成作答", value: String(results.value.length) },
  { label: "异常事件", value: "0" }
]);

onMounted(async () => {
  const [taskItems, candidateItems, resultItems] = await Promise.all([loadTasks(), loadCandidates(), loadResults()]);
  tasks.value = taskItems;
  candidates.value = candidateItems;
  results.value = resultItems;
});
</script>
```

```css
/* append to apps/web/src/styles.css */
.dashboard-page {
  display: grid;
  gap: 20px;
}

.dashboard-metrics {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 16px;
}

.dashboard-metric {
  padding: 20px;
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-lg);
  background: #fff;
}

.dashboard-metric p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.dashboard-metric strong {
  display: block;
  margin-top: 10px;
  font-size: 32px;
}

.dashboard-columns {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.section-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.section-head h2 {
  margin: 0;
  font-size: 20px;
}

.section-head p {
  margin: 8px 0 0;
  color: var(--text-secondary);
}
```

- [ ] **Step 4: Run the dashboard test to verify it passes**

Run: `npm --prefix apps/web run test -- src/views/admin/AdminDashboardView.spec.ts`

Expected: PASS with 1 passing test.

- [ ] **Step 5: Commit the dashboard redesign**

```bash
git add apps/web/src/views/admin/AdminDashboardView.vue apps/web/src/views/admin/AdminDashboardView.spec.ts apps/web/src/styles.css
git commit -m "feat: redesign admin dashboard"
```

## Task 5: Rebuild the Candidate List as a Filter + Table Surface

**Files:**
- Modify: `apps/web/src/views/admin/CandidateListView.vue`
- Create: `apps/web/src/views/admin/CandidateListView.spec.ts`
- Test: `apps/web/src/views/admin/CandidateListView.spec.ts`

- [ ] **Step 1: Write the failing candidate-list rendering test**

```ts
// apps/web/src/views/admin/CandidateListView.spec.ts
import { flushPromises, mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";

import CandidateListView from "./CandidateListView.vue";

vi.mock("../../lib/gateway", () => ({
  loadCandidates: vi.fn(async () => [
    {
      id: "c-1",
      taskId: "task-1",
      name: "张三",
      role: "后端工程师",
      city: "上海",
      status: "待审核",
      quality: "高",
      summary: "5 年 Java 后端经验",
      skills: ["Java", "MySQL"],
      paperId: "paper-1"
    }
  ])
}));

describe("CandidateListView", () => {
  it("renders filters and a table-driven candidate list", async () => {
    const wrapper = mount(CandidateListView, {
      global: {
        stubs: {
          RouterLink: { template: "<a><slot /></a>" },
          ElSelect: { template: "<div><slot /></div>" },
          ElOption: { props: ["label"], template: "<span>{{ label }}</span>" },
          ElInput: { template: "<input />" },
          ElTable: { props: ["data"], template: "<div><slot />{{ JSON.stringify(data) }}</div>" },
          ElTableColumn: { template: "<div><slot /></div>" },
          ElTag: { template: "<span><slot /></span>" }
        }
      }
    });

    await flushPromises();

    expect(wrapper.text()).toContain("候选人列表");
    expect(wrapper.text()).toContain("全部岗位");
    expect(wrapper.text()).toContain("张三");
    expect(wrapper.text()).toContain("待审核");
    expect(wrapper.text()).toContain("详情");
  });
});
```

- [ ] **Step 2: Run the candidate-list test to verify it fails**

Run: `npm --prefix apps/web run test -- src/views/admin/CandidateListView.spec.ts`

Expected: FAIL because the current page still renders the older card-grid layout instead of the approved filter + table surface.

- [ ] **Step 3: Replace the card grid with the new table page**

```vue
<!-- apps/web/src/views/admin/CandidateListView.vue -->
<template>
  <section class="candidate-page page-panel">
    <div class="section-head candidate-page__head">
      <div>
        <h2>候选人列表</h2>
        <p>按岗位、状态和风险优先级快速筛选候选人。</p>
      </div>
    </div>

    <div class="candidate-page__filters">
      <el-select v-model="roleFilter" placeholder="全部岗位" clearable>
        <el-option label="全部岗位" value="" />
        <el-option v-for="role in roleOptions" :key="role" :label="role" :value="role" />
      </el-select>

      <el-select v-model="statusFilter" placeholder="全部状态" clearable>
        <el-option label="全部状态" value="" />
        <el-option label="待审核" value="待审核" />
        <el-option label="待发卷" value="待发卷" />
        <el-option label="已发卷" value="已发卷" />
        <el-option label="已开考" value="已开考" />
        <el-option label="已交卷" value="已交卷" />
      </el-select>

      <el-input v-model="keyword" placeholder="搜索候选人 / 岗位 / 城市" clearable />
    </div>

    <el-table :data="filteredCandidates" stripe>
      <el-table-column prop="name" label="姓名" />
      <el-table-column prop="role" label="岗位" />
      <el-table-column prop="status" label="筛选状态">
        <template #default="{ row }">
          <el-tag :type="statusTypeMap[row.status] ?? 'info'">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="quality" label="解析状态" />
      <el-table-column prop="city" label="城市" />
      <el-table-column label="操作" width="220">
        <template #default="{ row }">
          <div class="candidate-page__actions">
            <RouterLink :to="{ name: 'admin-candidate-detail', params: { candidateId: row.id } }">详情</RouterLink>
            <RouterLink :to="{ name: 'admin-candidate-edit', params: { candidateId: row.id } }">编辑</RouterLink>
            <RouterLink :to="{ name: 'admin-paper-editor', params: { paperId: row.paperId ?? 'new' }, query: { candidateId: row.id, candidateName: row.name } }">
              发卷
            </RouterLink>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { loadCandidates, type CandidateCard } from "../../lib/gateway";

const keyword = ref("");
const roleFilter = ref("");
const statusFilter = ref("");
const candidates = ref<CandidateCard[]>([]);

const roleOptions = computed(() => Array.from(new Set(candidates.value.map((item) => item.role))));
const statusTypeMap: Record<string, "success" | "warning" | "primary" | "info" | "danger"> = {
  待审核: "warning",
  待发卷: "primary",
  已发卷: "info",
  已开考: "danger",
  已交卷: "success"
};

const filteredCandidates = computed(() => {
  const search = keyword.value.trim().toLowerCase();

  return candidates.value.filter((candidate) => {
    const matchesRole = !roleFilter.value || candidate.role === roleFilter.value;
    const matchesStatus = !statusFilter.value || candidate.status === statusFilter.value;
    const matchesKeyword =
      !search ||
      [candidate.name, candidate.role, candidate.city, candidate.summary].join(" ").toLowerCase().includes(search);

    return matchesRole && matchesStatus && matchesKeyword;
  });
});

onMounted(async () => {
  candidates.value = await loadCandidates();
});
</script>
```

```css
/* append to apps/web/src/styles.css */
.candidate-page {
  display: grid;
  gap: 18px;
}

.candidate-page__head {
  margin-bottom: 4px;
}

.candidate-page__filters {
  display: grid;
  grid-template-columns: 180px 180px minmax(220px, 320px);
  gap: 12px;
}

.candidate-page__actions {
  display: flex;
  gap: 12px;
  color: var(--brand-600);
  font-weight: 600;
}
```

- [ ] **Step 4: Run the candidate-list test to verify it passes**

Run: `npm --prefix apps/web run test -- src/views/admin/CandidateListView.spec.ts`

Expected: PASS with 1 passing test.

- [ ] **Step 5: Commit the candidate-list redesign**

```bash
git add apps/web/src/views/admin/CandidateListView.vue apps/web/src/views/admin/CandidateListView.spec.ts apps/web/src/styles.css
git commit -m "feat: redesign candidate list"
```

## Task 6: Verify the Phase-One UI Baseline and Remove Obvious Drift

**Files:**
- Modify: `apps/web/src/router/router.spec.ts`
- Modify: `apps/web/src/styles.css`
- Test: `apps/web/src/router/router.spec.ts`
- Test: `apps/web/src/views/admin/AdminLoginView.spec.ts`
- Test: `apps/web/src/views/admin/AdminDashboardView.spec.ts`
- Test: `apps/web/src/views/admin/CandidateListView.spec.ts`

- [ ] **Step 1: Write the final integration assertion into the router spec**

```ts
// append to apps/web/src/router/router.spec.ts
it("sends authenticated users from login to the new dashboard path", () => {
  const loginRoute = routes.find((route) => route.path === "/login");

  expect(loginRoute?.name).toBe("admin-login");
  expect(routes.some((route) => route.path === "/admin")).toBe(true);
});
```

- [ ] **Step 2: Run the targeted UI test suite to verify the new baseline**

Run: `npm --prefix apps/web run test -- src/router/router.spec.ts src/components/layout/adminNavigation.spec.ts src/views/admin/AdminLoginView.spec.ts src/views/admin/AdminDashboardView.spec.ts src/views/admin/CandidateListView.spec.ts`

Expected: FAIL if any of the redesigned routes, nav items, or sample pages have drifted during integration.

- [ ] **Step 3: Fix drift, tighten responsive rules, and keep the CSS aligned**

```css
/* finalize in apps/web/src/styles.css */
@media (max-width: 1200px) {
  .dashboard-columns,
  .dashboard-metrics {
    grid-template-columns: 1fr;
  }

  .candidate-page__filters,
  .login-screen {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 4: Run the full Phase-One verification commands**

Run: `npm --prefix apps/web run test -- src/router/router.spec.ts src/components/layout/adminNavigation.spec.ts src/views/admin/AdminLoginView.spec.ts src/views/admin/AdminDashboardView.spec.ts src/views/admin/CandidateListView.spec.ts && npm --prefix apps/web run build`

Expected:

- Vitest exits with all tests passing.
- `vite build` exits with code 0.

- [ ] **Step 5: Commit the verified Phase-One baseline**

```bash
git add apps/web/src/router/router.spec.ts apps/web/src/styles.css
git commit -m "chore: verify phase-one ui baseline"
```

## Self-Review

### Spec coverage

- New route skeleton from the approved UI spec: covered in Task 1.
- Element Plus-first implementation rule: covered in Tasks 1, 2, 4, and 5.
- New admin shell with full navigation hierarchy and placeholder pages: covered in Tasks 1 and 2.
- HR-only login redesign: covered in Task 3.
- Dashboard sample page: covered in Task 4.
- Candidate list sample page as a filter + table surface: covered in Task 5.
- Baseline verification and responsive cleanup: covered in Task 6.

### Placeholder scan

- No `TODO`, `TBD`, or “implement later” placeholders remain in the plan body.
- Placeholder routes are intentional product placeholders approved by the spec, not implementation placeholders in plan steps.

### Type consistency

- Route names are consistent across the router task and the UI tasks.
- Candidate list action links use the same `admin-candidate-detail`, `admin-candidate-edit`, and `admin-paper-editor` route names defined in Task 1.
- Dashboard and candidate list both continue to use the existing `CandidateCard`, `ScreeningTaskSummary`, and `ResultSummary` types from `src/lib/gateway.ts`.
