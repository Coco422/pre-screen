import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { createRouter, createMemoryHistory } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CandidateListView from "./CandidateListView.vue";

type CandidateRow = {
  id: string;
  taskId: string;
  name: string;
  role: string;
  city: string;
  status: string;
  quality: string;
  summary: string;
  skills: string[];
  resumeUploadedAt: string;
  resumeParseStatus: string;
  screeningStatus: string;
  riskFlag: string;
  riskLevel: string;
  updatedAt: string;
  paperSent: boolean;
  paperId?: string | null;
  resultId?: string | null;
  nextAction: {
    label: string;
    target: string;
  };
};

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason?: unknown) => void;
};

function createDeferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;

  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, resolve, reject };
}

function createRowStubs(row: CandidateRow) {
  return {
    RouterLink: { props: ["to"], template: "<a><slot /></a>" },
    ElSelect: {
      props: ["modelValue"],
      template: "<div class='select-stub' :data-model='modelValue'><slot /></div>"
    },
    ElOption: { props: ["label"], template: "<span class='option-stub'>{{ label }}</span>" },
    ElInput: { template: "<input />" },
    ElTable: {
      props: ["data"],
      template: "<div class='el-table'><slot />{{ JSON.stringify(data) }}</div>"
    },
    ElTableColumn: {
      props: ["label"],
      template: `<div>{{ label }}<slot :row='${JSON.stringify(row)}' /></div>`
    },
    ElTag: { template: "<span><slot /></span>" }
  };
}

const mocks = vi.hoisted(() => ({
  loadCandidates: vi.fn()
}));

vi.mock("../../lib/gateway", () => ({
  loadCandidates: mocks.loadCandidates
}));

function createTestRouter(taskId: string, status = "") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: "/admin/candidates",
        component: { template: "<div />" }
      }
    ]
  });

  return router.push({
    path: "/admin/candidates",
    query: status ? { taskId, status } : { taskId }
  }).then(() => router);
}

function buildCandidateRow(overrides: Partial<CandidateRow> = {}): CandidateRow {
  return {
    id: "c-1",
    taskId: "task-1",
    name: "张三",
    role: "前端工程师",
    city: "上海",
    status: "待审核",
    quality: "中",
    summary: "待复核项目经历",
    skills: ["Vue", "TypeScript"],
    resumeUploadedAt: "2026-04-20T10:00:00Z",
    resumeParseStatus: "parsed",
    screeningStatus: "待审核",
    riskFlag: "需核实",
    riskLevel: "medium",
    updatedAt: "2026-04-20T11:00:00Z",
    paperSent: false,
    paperId: null,
    resultId: null,
    nextAction: {
      label: "查看详情",
      target: "/admin/candidates/c-1"
    },
    ...overrides
  };
}

describe("CandidateListView", () => {
  beforeEach(() => {
    mocks.loadCandidates.mockReset();
  });

  it("renders filters and a table-driven candidate list", async () => {
    const row = buildCandidateRow();
    mocks.loadCandidates.mockResolvedValue([row]);

    const router = await createTestRouter("task-1");
    const wrapper = mount(CandidateListView, {
      global: {
        plugins: [router],
        stubs: createRowStubs(row)
      }
    });

    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain("候选人列表");
    expect(wrapper.text()).toContain("全部岗位");
    expect(wrapper.text()).toContain("全部状态");
    expect(wrapper.text()).toContain("全部审核");
    expect(wrapper.text()).toContain("全部发卷");
    expect(wrapper.text()).not.toContain("按岗位、状态和关键字快速筛选候选人");
    expect(wrapper.text()).toContain("PDF 上传时间");
    expect(wrapper.text()).toContain("解析状态");
    expect(wrapper.text()).toContain("筛选状态");
    expect(wrapper.text()).toContain("风险标记");
    expect(wrapper.text()).toContain("更新时间");
    expect(wrapper.text()).toContain("下一步");
    expect(wrapper.find(".el-table").exists()).toBe(true);
    expect(wrapper.text()).toContain("张三");
    expect(wrapper.text()).toContain("待审核");
    expect(wrapper.text()).toContain("需核实");
    expect(wrapper.text()).toContain("查看详情");
  });

  it("syncs deep link filters into the API request and filter controls", async () => {
    const row = buildCandidateRow({
      id: "c-2",
      taskId: "task-2",
      name: "李四",
      status: "待发卷",
      screeningStatus: "待发卷",
      paperId: "paper-2",
      nextAction: {
        label: "发卷",
        target: "/admin/papers/paper-2?candidateId=c-2"
      }
    });
    mocks.loadCandidates.mockResolvedValue([row]);

    const router = await createTestRouter("task-2", "待发卷");
    await router.push({
      path: "/admin/candidates",
      query: {
        taskId: "task-2",
        status: "待发卷",
        pendingReview: "true",
        paperSent: "false"
      }
    });
    const wrapper = mount(CandidateListView, {
      global: {
        plugins: [router],
        stubs: createRowStubs(row)
      }
    });

    await flushPromises();
    await nextTick();

    const selectModels = wrapper.findAll(".select-stub").map((node) => node.attributes("data-model"));
    const optionLabels = wrapper.findAll(".option-stub").map((node) => node.text());

    expect(mocks.loadCandidates).toHaveBeenLastCalledWith(
      expect.objectContaining({
        taskId: "task-2",
        status: "待发卷",
        pendingReview: true,
        paperSent: false
      })
    );
    expect(optionLabels).toContain("待发卷");
    expect(optionLabels).toContain("待审核");
    expect(optionLabels).toContain("未发卷");
    expect(selectModels[1]).toBe("待发卷");
    expect(selectModels[2]).toBe("true");
    expect(selectModels[3]).toBe("false");
    expect(wrapper.find(".el-table").text()).toContain("李四");
    expect(wrapper.find(".el-table").text()).toContain("待发卷");
  });

  it("keeps the latest task data when an older request resolves later", async () => {
    const requests = new Map<string, Deferred<CandidateRow[]>>();
    mocks.loadCandidates.mockImplementation((filters?: { taskId?: string } | string) => {
      const deferred = createDeferred<CandidateRow[]>();
      const taskId = typeof filters === "string" ? filters : filters?.taskId;
      requests.set(taskId ?? "default", deferred);
      return deferred.promise;
    });

    const router = await createTestRouter("task-1");
    const row = {
        ...buildCandidateRow({ id: "c-1", taskId: "task-1", name: "李四", status: "待发卷", screeningStatus: "待发卷" })
      };
    const wrapper = mount(CandidateListView, {
      global: {
        plugins: [router],
        stubs: createRowStubs(row)
      }
    });

    await nextTick();

    await router.push({
      path: "/admin/candidates",
      query: { taskId: "task-2" }
    });

    await nextTick();

    const oldRequest = requests.get("task-1");
    const newRequest = requests.get("task-2");

    expect(oldRequest).toBeTruthy();
    expect(newRequest).toBeTruthy();

    newRequest?.resolve([
      buildCandidateRow({ id: "c-new", taskId: "task-2", name: "李四", status: "待发卷", screeningStatus: "待发卷" })
    ]);

    await flushPromises();
    await nextTick();

    oldRequest?.resolve([
      buildCandidateRow({ id: "c-old", taskId: "task-1", name: "王五", role: "后端工程师" })
    ]);

    await flushPromises();
    await nextTick();

    expect(wrapper.find(".el-table").text()).toContain("李四");
    expect(wrapper.find(".el-table").text()).toContain("待发卷");
    expect(wrapper.find(".el-table").text()).not.toContain("王五");
    expect(wrapper.find(".candidate-page__state--error").exists()).toBe(false);
  });

  it("ignores a stale error after the latest task succeeds", async () => {
    const requests = new Map<string, Deferred<CandidateRow[]>>();
    mocks.loadCandidates.mockImplementation((filters?: { taskId?: string } | string) => {
      const deferred = createDeferred<CandidateRow[]>();
      const taskId = typeof filters === "string" ? filters : filters?.taskId;
      requests.set(taskId ?? "default", deferred);
      return deferred.promise;
    });

    const router = await createTestRouter("task-1");
    const row = {
        ...buildCandidateRow({ id: "c-1", taskId: "task-1", name: "李四", status: "待发卷", screeningStatus: "待发卷" })
      };
    const wrapper = mount(CandidateListView, {
      global: {
        plugins: [router],
        stubs: createRowStubs(row)
      }
    });

    await nextTick();

    await router.push({
      path: "/admin/candidates",
      query: { taskId: "task-2" }
    });

    await nextTick();

    const oldRequest = requests.get("task-1");
    const newRequest = requests.get("task-2");

    expect(oldRequest).toBeTruthy();
    expect(newRequest).toBeTruthy();

    newRequest?.resolve([
      buildCandidateRow({ id: "c-new", taskId: "task-2", name: "李四", status: "待发卷", screeningStatus: "待发卷" })
    ]);

    await flushPromises();
    await nextTick();

    oldRequest?.reject(new Error("old request failed"));

    await flushPromises();
    await nextTick();

    expect(wrapper.find(".el-table").text()).toContain("李四");
    expect(wrapper.find(".candidate-page__state--error").exists()).toBe(false);
  });
});
