import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import AdminLayout from "../layouts/AdminLayout.vue";

export const routes: RouteRecordRaw[] = [
  {
    path: "/",
    redirect: "/admin/candidates"
  },
  {
    path: "/admin/candidates",
    component: AdminLayout,
    children: [
      {
        path: "",
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
        component: () => import("../views/admin/CandidateDetailView.vue")
      }
    ]
  },
  {
    path: "/admin/papers/:paperId",
    component: AdminLayout,
    children: [
      {
        path: "",
        component: () => import("../views/admin/PaperEditorView.vue")
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
