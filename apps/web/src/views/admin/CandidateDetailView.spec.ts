import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CandidateDetailView from "./CandidateDetailView.vue";

type CandidateDetail = {
  id: string;
  taskId: string;
  name: string;
  role: string;
  email: string;
  city: string;
  phone: string;
  status: string;
  quality: string;
  skills: string[];
  hobbies: string[];
  heightCm: number | null;
  weightKg: number | null;
  availableInDays: number | null;
  projectSummary: string;
  projects: Array<{
    projectId: string;
    name: string;
    role: string;
    summary: string;
    techStack: string[];
    responsibilities: string[];
    achievements: string[];
    metrics: string[];
    sourcePages: number[];
    confidence: string;
  }>;
  analysis: {
    focusTopics: string[];
    strengths: string[];
    risks: string[];
    recommendedLanguages: string[];
    missingFields: string[];
  };
  processing: {
    stage: string;
    status: string;
    progress: number;
    message: string;
    errorMessage: string | null;
    steps: Record<string, { label?: string; status?: string }>;
  } | null;
  reviewNotes: string[];
  parseMetrics: {
    firstPageCharacters: number;
    multimodalPages: number;
    confidence: string;
  };
  paperId: string | null;
  invitationToken: string | null;
  resultId: string | null;
};

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
  reject: (reason?: unknown) => void;
};

type StorageMock = {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
  removeItem: (key: string) => void;
  clear: () => void;
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

function createStorageMock(): StorageMock {
  const store = new Map<string, string>();

  return {
    getItem(key) {
      return store.has(key) ? store.get(key) ?? null : null;
    },
    setItem(key, value) {
      store.set(key, value);
    },
    removeItem(key) {
      store.delete(key);
    },
    clear() {
      store.clear();
    }
  };
}

function buildCandidateDetail(overrides: Partial<CandidateDetail> = {}): CandidateDetail {
  return {
    id: "candidate-1",
    taskId: "task-1",
    name: "陈晓",
    role: "资深前端工程师",
    email: "chen@example.com",
    city: "上海",
    phone: "13800000000",
    status: "待发卷",
    quality: "高",
    skills: ["Vue 3", "TypeScript", "Node.js"],
    hobbies: ["羽毛球", "旅行"],
    heightCm: 172,
    weightKg: 60,
    availableInDays: 14,
    projectSummary: "负责中后台与招聘系统重构，推进组件化和接口治理。",
    projects: [
      {
        projectId: "project-1",
        name: "招聘中台",
        role: "前端负责人",
        summary: "搭建统一招聘控制台，支撑 20+ 业务流程。",
        techStack: ["Vue", "TypeScript", "Vite"],
        responsibilities: ["主导控制台架构", "统一表单规范"],
        achievements: ["首屏提速 35%", "缺陷率下降 22%"],
        metrics: ["10 周交付", "覆盖 12 条业务线"],
        sourcePages: [2, 3],
        confidence: "high"
      }
    ],
    analysis: {
      focusTopics: ["复杂表单", "权限体系"],
      strengths: ["交付节奏稳定", "业务抽象能力强"],
      risks: ["跨端经验较少"],
      recommendedLanguages: ["TypeScript", "Go"],
      missingFields: ["期望薪资"]
    },
    processing: null,
    reviewNotes: ["需要补充薪资预期", "优先确认到岗时间"],
    parseMetrics: {
      firstPageCharacters: 260,
      multimodalPages: 1,
      confidence: "高"
    },
    paperId: "paper-1",
    invitationToken: "invite-1",
    resultId: null,
    ...overrides
  };
}

const mocks = vi.hoisted(() => ({
  loadCandidateDetail: vi.fn()
}));

vi.mock("../../lib/gateway", () => ({
  loadCandidateDetail: mocks.loadCandidateDetail
}));

async function mountView(candidateId = "candidate-1") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: "/admin/candidates/:candidateId",
        component: CandidateDetailView
      }
    ]
  });

  await router.push(`/admin/candidates/${candidateId}`);
  await router.isReady();

  return mount(CandidateDetailView, {
    global: {
      plugins: [router],
      stubs: {
        RouterLink: {
          props: ["to"],
          template: "<a :data-target='JSON.stringify(to)'><slot /></a>"
        },
        AdminToneBadge: {
          props: ["label"],
          template: "<span class='tone-badge'>{{ label }}</span>"
        },
        AdminScoreBar: {
          props: ["label", "value", "detail"],
          template: "<div class='score-bar'>{{ label }} {{ value }} {{ detail }}</div>"
        }
      }
    }
  });
}

describe("CandidateDetailView", () => {
  beforeEach(() => {
    mocks.loadCandidateDetail.mockReset();
    Object.defineProperty(window, "localStorage", {
      value: createStorageMock(),
      configurable: true
    });
    window.localStorage.clear();
  });

  it("shows a loading state before the candidate detail resolves", async () => {
    const request = createDeferred<CandidateDetail>();
    mocks.loadCandidateDetail.mockReturnValueOnce(request.promise);

    const wrapper = await mountView();

    expect(wrapper.text()).toContain("正在加载候选人详情");
    expect(wrapper.find(".candidate-console").exists()).toBe(false);
    expect(wrapper.text()).not.toContain("详情页会以当前路由候选人为准");

    request.resolve(buildCandidateDetail());
    await flushPromises();
  });

  it("renders a three-column review console and overlays the local draft", async () => {
    window.localStorage.setItem(
      "admin-candidate-draft:candidate-1",
      JSON.stringify({
        name: "陈晓（草稿）",
        email: "draft@example.com",
        skills: ["TypeScript", "Node.js", "Prompt Design"],
        projectSummary: "草稿版项目摘要",
        reviewNotes: ["草稿备注：优先确认管理跨度"]
      })
    );
    mocks.loadCandidateDetail.mockResolvedValue(buildCandidateDetail());

    const wrapper = await mountView();

    await flushPromises();
    await nextTick();

    expect(wrapper.find(".review-board").exists()).toBe(true);
    expect(wrapper.findAll(".review-panel")).toHaveLength(3);
    expect(wrapper.text()).toContain("基本信息");
    expect(wrapper.text()).toContain("结构化档案");
    expect(wrapper.text()).toContain("风险与操作");
    expect(wrapper.text()).toContain("陈晓（草稿）");
    expect(wrapper.text()).toContain("draft@example.com");
    expect(wrapper.text()).toContain("Prompt Design");
    expect(wrapper.text()).toContain("草稿版项目摘要");
    expect(wrapper.text()).toContain("复杂表单");
    expect(wrapper.text()).toContain("招聘中台");
    expect(wrapper.text()).toContain("草稿备注：优先确认管理跨度");
    expect(wrapper.text()).toContain("编辑画像");
    expect(wrapper.find(".hero-panel").exists()).toBe(false);
  });
});
