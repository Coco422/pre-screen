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
    meta: {
      title: "HR 登录"
    },
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
        path: "workbench",
        name: "admin-workbench",
        redirect: "/admin/dashboard"
      },
      {
        path: "dashboard",
        name: "admin-dashboard",
        meta: {
          title: "工作台"
        },
        component: () => import("../views/admin/AdminDashboardView.vue")
      },
      {
        path: "tasks",
        name: "admin-tasks",
        meta: {
          title: "任务中心"
        },
        component: () => import("../views/shared/PlaceholderView.vue"),
        props: {
          description: "任务中心将在后续阶段重构。",
          iconLabel: "Tasks"
        }
      },
      {
        path: "papers",
        name: "admin-papers",
        meta: {
          title: "考卷管理"
        },
        component: () => import("../views/shared/PlaceholderView.vue"),
        props: {
          description: "考卷管理列表将在后续阶段重构。",
          iconLabel: "Papers"
        }
      },
      {
        path: "tasks/new",
        name: "admin-task-create",
        meta: {
          title: "新建筛选任务"
        },
        component: () => import("../views/admin/TaskCreateView.vue")
      },
      {
        path: "tasks/:taskId",
        name: "admin-task-detail",
        meta: {
          title: "任务详情"
        },
        component: () => import("../views/admin/TaskDetailView.vue")
      },
      {
        path: "candidates",
        name: "admin-candidates",
        meta: {
          title: "候选人"
        },
        component: () => import("../views/admin/CandidateListView.vue")
      },
      {
        path: "candidates/:candidateId",
        name: "admin-candidate-detail",
        meta: {
          title: "候选人详情"
        },
        component: () => import("../views/admin/CandidateDetailView.vue")
      },
      {
        path: "candidates/:candidateId/edit",
        name: "admin-candidate-edit",
        meta: {
          title: "编辑画像"
        },
        component: () => import("../views/admin/CandidateEditView.vue")
      },
      {
        path: "papers/:paperId",
        name: "admin-paper-editor",
        meta: {
          title: "考卷管理"
        },
        component: () => import("../views/admin/PaperEditorView.vue")
      },
      {
        path: "results",
        name: "admin-results",
        meta: {
          title: "结果中心"
        },
        component: () => import("../views/admin/ResultListView.vue")
      },
      {
        path: "results/:resultId",
        name: "admin-result-detail",
        meta: {
          title: "结果详情"
        },
        component: () => import("../views/admin/ResultDetailView.vue")
      },
      {
        path: "risk",
        name: "admin-risk",
        meta: {
          title: "风险管理"
        },
        component: () => import("../views/shared/PlaceholderView.vue"),
        props: {
          description: "风险管理将在后续阶段重构。",
          iconLabel: "Risk"
        }
      },
      {
        path: "settings",
        name: "admin-settings",
        meta: {
          title: "系统设置"
        },
        component: () => import("../views/shared/PlaceholderView.vue"),
        props: {
          description: "系统设置将在后续阶段重构。",
          iconLabel: "Settings"
        }
      }
    ]
  },
  {
    path: "/exam/:token",
    redirect: (to) => `/exam/${String(to.params.token)}/start`
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
