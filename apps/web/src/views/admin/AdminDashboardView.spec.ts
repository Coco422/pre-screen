import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AdminDashboardView from "./AdminDashboardView.vue";

const mocks = vi.hoisted(() => ({
  loadTasks: vi.fn(),
  loadCandidates: vi.fn(),
  loadResults: vi.fn()
}));

vi.mock("../../lib/gateway", () => ({
  loadTasks: mocks.loadTasks,
  loadCandidates: mocks.loadCandidates,
  loadResults: mocks.loadResults
}));

const routerLinkStub = {
  props: ["to"],
  template: "<a><slot /></a>"
};

const tableStub = {
  props: ["data"],
  template:
    "<div class='table-stub'><div v-for='item in data' :key='item.id ?? item.title ?? item.resultId' class='table-row'>{{ item.name ?? item.title ?? item.candidateName }} {{ item.status ?? '' }}</div></div>"
};

const tableColumnStub = {
  template: "<div />"
};

function mountDashboard() {
  return mount(AdminDashboardView, {
    global: {
      stubs: {
        RouterLink: routerLinkStub,
        ElTable: tableStub,
        ElTableColumn: tableColumnStub
      }
    }
  });
}

describe("AdminDashboardView", () => {
  beforeEach(() => {
    mocks.loadTasks.mockReset();
    mocks.loadCandidates.mockReset();
    mocks.loadResults.mockReset();
  });

  it("shows only actionable candidates in the metric and list", async () => {
    mocks.loadTasks.mockResolvedValue([
      {
        id: "task-1",
        title: "前端筛选",
        role: "Frontend Engineer",
        status: "进行中",
        candidateCount: 4,
        uploadCount: 2,
        createdAt: "2026-04-21T09:00:00Z"
      }
    ]);
    mocks.loadCandidates.mockResolvedValue([
      {
        id: "c-1",
        taskId: "task-1",
        name: "Ada",
        role: "Frontend Engineer",
        city: "Shanghai",
        status: "待审核",
        quality: "高",
        summary: "待审核候选人",
        skills: [],
        paperId: null,
        resultId: null
      },
      {
        id: "c-2",
        taskId: "task-1",
        name: "Ben",
        role: "Frontend Engineer",
        city: "Shenzhen",
        status: "待发卷",
        quality: "高",
        summary: "待发卷候选人",
        skills: [],
        paperId: null,
        resultId: null
      },
      {
        id: "c-3",
        taskId: "task-1",
        name: "Cora",
        role: "Frontend Engineer",
        city: "Beijing",
        status: "已发卷",
        quality: "高",
        summary: "已发卷候选人",
        skills: [],
        paperId: "paper-1",
        resultId: null
      },
      {
        id: "c-4",
        taskId: "task-1",
        name: "Dylan",
        role: "Frontend Engineer",
        city: "Hangzhou",
        status: "已完成",
        quality: "高",
        summary: "不应出现在待处理列表",
        skills: [],
        paperId: "paper-2",
        resultId: "result-1"
      }
    ]);
    mocks.loadResults.mockResolvedValue([
      {
        resultId: "result-1",
        candidateId: "c-4",
        candidateName: "Dylan",
        role: "Frontend Engineer",
        submittedAt: "2026-04-21T10:00:00Z",
        totalScore: 82,
        status: "已交卷"
      }
    ]);

    const wrapper = mountDashboard();
    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain("待处理候选人");
    expect(wrapper.text()).toContain("3");
    expect(wrapper.text()).toContain("Ada 待审核");
    expect(wrapper.text()).toContain("Ben 待发卷");
    expect(wrapper.text()).toContain("Cora 已发卷");
    expect(wrapper.text()).not.toContain("Dylan 已完成");
  });

  it("keeps successful dashboard sections and shows an error banner when one request fails", async () => {
    mocks.loadTasks.mockRejectedValue(new Error("task failed"));
    mocks.loadCandidates.mockResolvedValue([
      {
        id: "c-1",
        taskId: "task-1",
        name: "Ada",
        role: "Frontend Engineer",
        city: "Shanghai",
        status: "待审核",
        quality: "高",
        summary: "待审核候选人",
        skills: [],
        paperId: null,
        resultId: null
      }
    ]);
    mocks.loadResults.mockResolvedValue([
      {
        resultId: "result-1",
        candidateId: "c-1",
        candidateName: "Ada",
        role: "Frontend Engineer",
        submittedAt: "2026-04-21T10:00:00Z",
        totalScore: 91,
        status: "已交卷"
      }
    ]);

    const wrapper = mountDashboard();
    await flushPromises();
    await nextTick();

    expect(wrapper.get('[role="alert"]').text()).toContain("任务数据加载失败，已显示可用内容。");
    expect(wrapper.text()).toContain("待处理候选人");
    expect(wrapper.text()).toContain("1");
    expect(wrapper.text()).toContain("Ada 待审核");
    expect(wrapper.text()).toContain("Ada 已交卷");
  });
});
