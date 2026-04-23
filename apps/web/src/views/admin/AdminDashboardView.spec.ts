import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AdminDashboardView from "./AdminDashboardView.vue";

const mocks = vi.hoisted(() => ({
  loadDashboard: vi.fn()
}));

vi.mock("../../lib/gateway", () => ({
  loadDashboard: mocks.loadDashboard
}));

const routerLinkStub = {
  props: ["to"],
  template: "<a><slot /></a>"
};

function mountDashboard() {
  return mount(AdminDashboardView, {
    global: {
      stubs: {
        RouterLink: routerLinkStub
      }
    }
  });
}

describe("AdminDashboardView", () => {
  beforeEach(() => {
    mocks.loadDashboard.mockReset();
  });

  it("shows the dashboard metrics and three priority lists from the dashboard api", async () => {
    mocks.loadDashboard.mockResolvedValue({
      metrics: {
        screeningCandidateCount: 3,
        pendingPublishCount: 2,
        examInProgressCount: 1,
        submittedCount: 4,
        screeningCompletedCount: 6
      },
      screeningCandidates: [
        {
          candidateId: "c-1",
          name: "Ada",
          role: "前端工程师",
          status: "待审核",
          resumeUploadedAt: "2026-04-20T10:00:00Z",
          target: "/admin/candidates/c-1"
        }
      ],
      pendingPublishCandidates: [
        {
          candidateId: "c-2",
          name: "Ben",
          role: "前端工程师",
          status: "待发卷",
          profileCompletedAt: "2026-04-21T10:00:00Z",
          target: "/admin/papers/p-1?candidateId=c-2"
        }
      ],
      submittedResults: [
        {
          resultId: "r-1",
          candidateId: "c-3",
          candidateName: "Cora",
          role: "前端工程师",
          status: "已交卷",
          submittedAt: "2026-04-22T10:00:00Z",
          totalScore: 88,
          target: "/admin/results/r-1"
        }
      ]
    });

    const wrapper = mountDashboard();
    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain("筛选中候选人");
    expect(wrapper.text()).toContain("3");
    expect(wrapper.text()).toContain("待发卷人数");
    expect(wrapper.text()).toContain("进行中考试");
    expect(wrapper.text()).toContain("已交卷");
    expect(wrapper.text()).toContain("已完成筛选");
    expect(wrapper.text()).toContain("Ada");
    expect(wrapper.text()).toContain("Ben");
    expect(wrapper.text()).toContain("Cora");
  });

  it("shows an error banner when the dashboard api fails", async () => {
    mocks.loadDashboard.mockRejectedValue(new Error("dashboard failed"));

    const wrapper = mountDashboard();
    await flushPromises();
    await nextTick();

    expect(wrapper.get('[role="alert"]').text()).toContain("工作台数据加载失败");
  });
});
