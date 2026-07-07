import { flushPromises, mount } from "@vue/test-utils";
import { defineComponent, h, inject, nextTick, provide, ref, toRef, type PropType, type Ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import TaskListView from "./TaskListView.vue";

type TaskRow = {
  id: string;
  title: string;
  role: string;
  status: string;
  candidateCount: number;
  uploadCount: number;
  createdAt: string;
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

const tableRowsKey = Symbol("tableRows");

function createStubs() {
  return {
    RouterLink: {
      name: "RouterLink",
      props: {
        to: {
          type: Object as PropType<Record<string, unknown>>,
          required: true
        },
        custom: Boolean
      },
      template:
        "<slot v-if='custom' :href='`#${JSON.stringify(to)}`' :navigate='() => undefined' /><a v-else class='router-link-stub' :data-to='JSON.stringify(to)'><slot /></a>"
    },
    ElButton: {
      name: "ElButton",
      props: ["type", "size", "link", "plain", "tag", "href"],
      template:
        "<button class='el-button-stub' :data-type='type' :data-size='size' :data-link='link' :data-plain='plain' :data-tag='tag' :data-href='href'><slot /></button>"
    },
    ElSelect: {
      name: "ElSelect",
      props: ["modelValue", "placeholder"],
      emits: ["update:modelValue"],
      template:
        "<div class='select-stub' :data-model='modelValue' :data-placeholder='placeholder'><slot /></div>"
    },
    ElOption: {
      name: "ElOption",
      props: ["label", "value"],
      template: "<span class='option-stub' :data-value='value'>{{ label }}</span>"
    },
    ElInput: {
      name: "ElInput",
      props: ["modelValue", "placeholder"],
      emits: ["update:modelValue"],
      template:
        "<input class='input-stub' :value='modelValue' :placeholder='placeholder' @input=\"$emit('update:modelValue', $event.target.value)\" />"
    },
    ElTable: defineComponent({
      name: "ElTable",
      props: {
        data: {
          type: Array as PropType<TaskRow[]>,
          default: () => []
        },
        emptyText: String
      },
      setup(props, { slots }) {
        provide(tableRowsKey, toRef(props, "data"));

        return () => h("div", { class: "el-table" }, slots.default?.());
      }
    }),
    ElTableColumn: defineComponent({
      name: "ElTableColumn",
      props: ["label", "minWidth", "width", "prop", "fixed"],
      setup(props, { slots }) {
        const rows = inject<Ref<TaskRow[]>>(tableRowsKey, ref<TaskRow[]>([]));

        return () =>
          h(
            "div",
            { class: "table-column-stub", "data-label": props.label },
            [
              h("span", { class: "table-column-stub__label" }, props.label),
              ...rows.value.map((row) =>
                h(
                  "div",
                  {
                    class: "table-cell-stub",
                    "data-column-label": props.label,
                    "data-row-id": row.id
                  },
                  slots.default?.({ row }) ?? String(row[props.prop as keyof TaskRow] ?? "")
                )
              )
            ]
          );
      }
    }),
    ElTag: {
      name: "ElTag",
      props: ["type", "effect"],
      template: "<span class='tag-stub' :data-type='type'><slot /></span>"
    },
    ElProgress: {
      name: "ElProgress",
      props: ["percentage", "showText", "strokeWidth", "status"],
      template:
        "<div class='el-progress-stub' :data-percentage='percentage' :data-status='status'>{{ percentage }}%</div>"
    },
    ElEmpty: {
      name: "ElEmpty",
      props: ["description"],
      template: "<div class='el-empty'>{{ description }}<slot /></div>"
    },
    ElAlert: {
      name: "ElAlert",
      props: ["title", "description", "type", "closable"],
      template: "<div class='el-alert' role='alert'>{{ title }} {{ description }}<slot /></div>"
    },
    ElSkeleton: {
      name: "ElSkeleton",
      props: ["rows", "animated"],
      template: "<div class='el-skeleton'>正在加载任务列表</div>"
    }
  };
}

const mocks = vi.hoisted(() => ({
  loadTasks: vi.fn()
}));

vi.mock("../../lib/gateway", () => ({
  loadTasks: mocks.loadTasks
}));

function mountTaskList() {
  return mount(TaskListView, {
    global: {
      stubs: createStubs()
    }
  });
}

describe("TaskListView", () => {
  beforeEach(() => {
    mocks.loadTasks.mockReset();
  });

  it("renders the tightened task table with a derived owner and row actions", async () => {
    const deferred = createDeferred<TaskRow[]>();
    mocks.loadTasks.mockReturnValue(deferred.promise);

    const rows = [
      {
        id: "task-1",
        title: "前端开发首轮筛选",
        role: "前端开发工程师",
        status: "进行中",
        candidateCount: 3,
        uploadCount: 5,
        createdAt: "2026-04-21T09:00:00Z"
      },
      {
        id: "task-2",
        title: "后端开发补录",
        role: "后端开发工程师",
        status: "已完成",
        candidateCount: 8,
        uploadCount: 8,
        createdAt: "2026-04-20T09:00:00Z"
      },
      {
        id: "task-3",
        title: "前端开发终面池",
        role: "前端开发工程师",
        status: "待上传",
        candidateCount: 0,
        uploadCount: 0,
        createdAt: "2026-04-19T09:00:00Z"
      }
    ] satisfies TaskRow[];

    const wrapper = mountTaskList();

    await nextTick();

    expect(wrapper.find(".el-skeleton").exists()).toBe(true);

    deferred.resolve(rows);
    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain("任务中心");
    expect(wrapper.text()).toContain("筛选任务列表");
    expect(wrapper.text()).toContain("条任务");
    expect(wrapper.text()).toContain("新建任务");
    expect(wrapper.find(".task-list-page__create").exists()).toBe(true);
    expect(wrapper.text()).toContain("任务名称");
    expect(wrapper.text()).toContain("岗位");
    expect(wrapper.text()).toContain("负责人");
    expect(wrapper.text()).toContain("创建时间");
    expect(wrapper.text()).toContain("候选人数");
    expect(wrapper.text()).toContain("进度");
    expect(wrapper.text()).toContain("状态");
    expect(wrapper.text()).toContain("操作");
    expect(wrapper.text()).toContain("前端开发首轮筛选");
    expect(wrapper.text()).toContain("后端开发补录");
    expect(wrapper.text()).toContain("前端开发终面池");
    expect(wrapper.text()).toContain("系统分配 ·");
    expect(wrapper.text()).toContain("2026-04-21 17:00");
    expect(wrapper.text()).toContain("3 人");
    expect(wrapper.text()).toContain("60%");
    expect(wrapper.text()).toContain("100%");
    expect(wrapper.text()).toContain("0%");
    expect(wrapper.text()).toContain("已完成");
    expect(wrapper.text()).toContain("待上传");
    expect(wrapper.text()).not.toContain("简历");

    const createTargets = wrapper
      .findAllComponents({ name: "RouterLink" })
      .map((component) => JSON.stringify(component.props("to")));

    expect(createTargets.some((target) => target?.includes("\"name\":\"admin-task-create\""))).toBe(true);
    expect(wrapper.findAll(".task-list-page__action")).toHaveLength(rows.length);

    const titleLinks = wrapper.findAll(".task-cell__link");
    expect(titleLinks).toHaveLength(rows.length);
    expect(titleLinks[0]?.attributes("data-to")).toContain("\"name\":\"admin-task-detail\"");
    expect(titleLinks[0]?.attributes("data-to")).toContain("\"taskId\":\"task-1\"");
    expect(titleLinks[1]?.attributes("data-to")).toContain("\"taskId\":\"task-2\"");
    expect(titleLinks[2]?.attributes("data-to")).toContain("\"taskId\":\"task-3\"");
  });

  it("filters tasks by role, status, and keyword", async () => {
    mocks.loadTasks.mockResolvedValue([
      {
        id: "task-1",
        title: "前端开发首轮筛选",
        role: "前端开发工程师",
        status: "进行中",
        candidateCount: 3,
        uploadCount: 5,
        createdAt: "2026-04-21T09:00:00Z"
      },
      {
        id: "task-2",
        title: "后端开发补录",
        role: "后端开发工程师",
        status: "已完成",
        candidateCount: 8,
        uploadCount: 8,
        createdAt: "2026-04-20T09:00:00Z"
      },
      {
        id: "task-3",
        title: "前端开发终面池",
        role: "前端开发工程师",
        status: "待上传",
        candidateCount: 0,
        uploadCount: 0,
        createdAt: "2026-04-19T09:00:00Z"
      }
    ] satisfies TaskRow[]);

    const wrapper = mountTaskList();

    await flushPromises();
    await nextTick();

    const selects = wrapper.findAllComponents({ name: "ElSelect" });
    await selects[0]?.vm.$emit("update:modelValue", "前端开发工程师");
    await selects[1]?.vm.$emit("update:modelValue", "进行中");
    await wrapper.get(".input-stub").setValue("首轮");
    await nextTick();

    const tableText = wrapper.find(".el-table").text();
    const detailLinks = wrapper.findAll(".task-cell__link");

    expect(tableText).toContain("前端开发首轮筛选");
    expect(tableText).not.toContain("后端开发补录");
    expect(tableText).not.toContain("前端开发终面池");
    expect(tableText).toContain("60%");
    expect(tableText).toContain("3/5");
    expect(detailLinks).toHaveLength(1);
    expect(detailLinks[0]?.attributes("data-to")).toContain("\"taskId\":\"task-1\"");
  });

  it("shows an Element Plus empty state when there are no tasks", async () => {
    mocks.loadTasks.mockResolvedValue([]);

    const wrapper = mountTaskList();

    await flushPromises();
    await nextTick();

    expect(wrapper.find(".el-empty").text()).toContain("暂无任务");
  });

  it("shows an Element Plus error state when loading fails", async () => {
    mocks.loadTasks.mockRejectedValue(new Error("task failed"));

    const wrapper = mountTaskList();

    await flushPromises();
    await nextTick();

    expect(wrapper.get('[role="alert"]').text()).toContain("任务列表加载失败");
  });
});
