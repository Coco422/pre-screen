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
        name: "admin-workbench",
        meta: {
          title: "工作台"
        },
        component: () => import("../views/admin/AdminWorkbenchView.vue")
      }
    ]
  },
  {
    path: "/admin/tasks/new",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "admin-task-create",
        meta: {
          title: "新建筛选任务"
        },
        component: () => import("../views/admin/TaskCreateView.vue")
      }
    ]
  },
  {
    path: "/admin/tasks/:taskId",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "admin-task-detail",
        meta: {
          title: "任务详情"
        },
        component: () => import("../views/admin/TaskDetailView.vue")
      }
    ]
  },
  {
    path: "/admin/candidates",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "admin-candidates",
        meta: {
          title: "候选人"
        },
        component: () => import("../views/admin/CandidateListView.vue")
      }
    ]
  },
  {
    path: "/admin/candidates/:candidateId",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "admin-candidate-detail",
        meta: {
          title: "候选人详情"
        },
        component: () => import("../views/admin/CandidateDetailView.vue")
      }
    ]
  },
  {
    path: "/admin/candidates/:candidateId/edit",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "admin-candidate-edit",
        meta: {
          title: "编辑画像"
        },
        component: () => import("../views/admin/CandidateEditView.vue")
      }
    ]
  },
  {
    path: "/admin/papers/:paperId",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "admin-paper-editor",
        meta: {
          title: "考卷发布"
        },
        component: () => import("../views/admin/PaperEditorView.vue")
      }
    ]
  },
  {
    path: "/admin/results",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "admin-results",
        meta: {
          title: "作答结果"
        },
        component: () => import("../views/admin/ResultListView.vue")
      }
    ]
  },
  {
    path: "/admin/results/:resultId",
    component: AdminLayout,
    children: [
      {
        path: "",
        name: "admin-result-detail",
        meta: {
          title: "结果详情"
        },
        component: () => import("../views/admin/ResultDetailView.vue")
      }
    ]
  },
  {
    path: "/exam/:token",
    component: () => import("../views/exam/ExamShellView.vue")
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
    return "/admin";
  }

  return true;
});
