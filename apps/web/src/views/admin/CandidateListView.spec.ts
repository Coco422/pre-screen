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
  paperId: string;
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

function createRowStubs(row: Pick<CandidateRow, "id" | "name" | "paperId" | "status" | "quality" | "city">) {
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

describe("CandidateListView", () => {
  beforeEach(() => {
    mocks.loadCandidates.mockReset();
  });

  it("renders filters and a table-driven candidate list", async () => {
    mocks.loadCandidates.mockResolvedValue([
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
      } satisfies CandidateRow
    ]);

    const router = await createTestRouter("task-1");
    const row = {
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
    } satisfies CandidateRow;
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
    expect(wrapper.text()).toContain("筛选状态");
    expect(wrapper.find(".el-table").exists()).toBe(true);
    expect(wrapper.text()).toContain("张三");
    expect(wrapper.text()).toContain("待审核");
    expect(wrapper.text()).toContain("详情");
  });

  it("syncs the completed status deep link into the select and filter set", async () => {
    mocks.loadCandidates.mockResolvedValue([
      {
        id: "c-2",
        taskId: "task-2",
        name: "李四",
        role: "前端工程师",
        city: "北京",
        status: "已完成",
        quality: "高",
        summary: "已完成候选人",
        skills: ["Vue"],
        paperId: "paper-2"
      } satisfies CandidateRow
    ]);

    const router = await createTestRouter("task-2", "已完成");
    const row = {
      id: "c-2",
      taskId: "task-2",
      name: "李四",
      role: "前端工程师",
      city: "北京",
      status: "已完成",
      quality: "高",
      summary: "已完成候选人",
      skills: ["Vue"],
      paperId: "paper-2"
    } satisfies CandidateRow;
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

    expect(optionLabels).toContain("已完成");
    expect(selectModels[1]).toBe("已完成");
    expect(wrapper.find(".el-table").text()).toContain("李四");
    expect(wrapper.find(".el-table").text()).toContain("已完成");
  });

  it("keeps the latest task data when an older request resolves later", async () => {
    const requests = new Map<string, Deferred<CandidateRow[]>>();
    mocks.loadCandidates.mockImplementation((taskId?: string) => {
      const deferred = createDeferred<CandidateRow[]>();
      requests.set(taskId ?? "default", deferred);
      return deferred.promise;
    });

    const router = await createTestRouter("task-1");
    const row = {
      id: "c-1",
      taskId: "task-1",
      name: "李四",
      role: "前端工程师",
      city: "北京",
      status: "待发卷",
      quality: "中",
      summary: "最新任务的数据",
      skills: ["Vue"],
      paperId: "paper-2"
    } satisfies CandidateRow;
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
      {
        id: "c-new",
        taskId: "task-2",
        name: "李四",
        role: "前端工程师",
        city: "北京",
        status: "待发卷",
        quality: "中",
        summary: "最新任务的数据",
        skills: ["Vue"],
        paperId: "paper-2"
      }
    ]);

    await flushPromises();
    await nextTick();

    oldRequest?.resolve([
      {
        id: "c-old",
        taskId: "task-1",
        name: "王五",
        role: "后端工程师",
        city: "上海",
        status: "待审核",
        quality: "高",
        summary: "旧任务的数据",
        skills: ["Java"],
        paperId: "paper-1"
      }
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
    mocks.loadCandidates.mockImplementation((taskId?: string) => {
      const deferred = createDeferred<CandidateRow[]>();
      requests.set(taskId ?? "default", deferred);
      return deferred.promise;
    });

    const router = await createTestRouter("task-1");
    const row = {
      id: "c-1",
      taskId: "task-1",
      name: "李四",
      role: "前端工程师",
      city: "北京",
      status: "待发卷",
      quality: "中",
      summary: "最新任务的数据",
      skills: ["Vue"],
      paperId: "paper-2"
    } satisfies CandidateRow;
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
      {
        id: "c-new",
        taskId: "task-2",
        name: "李四",
        role: "前端工程师",
        city: "北京",
        status: "待发卷",
        quality: "中",
        summary: "最新任务的数据",
        skills: ["Vue"],
        paperId: "paper-2"
      }
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
