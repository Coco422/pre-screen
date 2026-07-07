import { flushPromises, mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { createMemoryHistory, createRouter } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";

import CandidateEditView from "./CandidateEditView.vue";

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

type CandidateApiResponse = {
  id: string;
  task_id: string;
  name: string;
  role: string;
  email: string;
  city: string;
  phone: string;
  status: string;
  quality: string;
  skills: string[];
  hobbies: string[];
  height_cm: number | null;
  weight_kg: number | null;
  available_in_days: number | null;
  project_summary: string;
  projects: Array<{
    project_id: string;
    name: string;
    role: string;
    summary: string;
    tech_stack: string[];
    responsibilities: string[];
    achievements: string[];
    metrics: string[];
    source_pages: number[];
    confidence: string;
  }>;
  analysis: {
    focus_topics: string[];
    strengths: string[];
    risks: string[];
    recommended_languages: string[];
    missing_fields: string[];
  };
  processing: CandidateDetail["processing"];
  review_notes: string[];
  parse_metrics: {
    first_page_characters: number;
    multimodal_pages: number;
    confidence: string;
  };
  paper_id: string | null;
  invitation_token: string | null;
  result_id: string | null;
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
    skills: ["Vue 3", "TypeScript"],
    hobbies: ["羽毛球", "旅行"],
    heightCm: 172,
    weightKg: 60,
    availableInDays: 14,
    projectSummary: "负责中后台与招聘系统重构。",
    projects: [],
    analysis: {
      focusTopics: ["复杂表单"],
      strengths: ["交付稳定"],
      risks: ["需要确认薪资"],
      recommendedLanguages: ["TypeScript"],
      missingFields: ["期望薪资"]
    },
    processing: null,
    reviewNotes: ["需要补充薪资预期"],
    parseMetrics: {
      firstPageCharacters: 260,
      multimodalPages: 0,
      confidence: "高"
    },
    paperId: "paper-1",
    invitationToken: "invite-1",
    resultId: null,
    ...overrides
  };
}

const mocks = vi.hoisted(() => ({
  loadCandidateDetail: vi.fn(),
  updateCandidateDetail: vi.fn()
}));

const fetchMock = vi.fn();

vi.mock("../../lib/gateway", () => ({
  loadCandidateDetail: mocks.loadCandidateDetail,
  updateCandidateDetail: mocks.updateCandidateDetail
}));

async function mountView(candidateId = "candidate-1") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: "/admin/candidates/:candidateId/edit",
        component: CandidateEditView
      }
    ]
  });

  await router.push(`/admin/candidates/${candidateId}/edit`);
  await router.isReady();

  const wrapper = mount(CandidateEditView, {
    global: {
      plugins: [router],
      stubs: {
        RouterLink: {
          props: ["to"],
          template: "<a :data-target='JSON.stringify(to)'><slot /></a>"
        }
      }
    }
  });

  return { wrapper, router };
}

function fieldValue(wrapper: Awaited<ReturnType<typeof mountView>>["wrapper"], selector: string) {
  return (wrapper.get(selector).element as HTMLInputElement | HTMLTextAreaElement).value;
}

function buildCandidateApiResponse(overrides: Partial<CandidateDetail> = {}): CandidateApiResponse {
  const detail = buildCandidateDetail(overrides);

  return {
    id: detail.id,
    task_id: detail.taskId,
    name: detail.name,
    role: detail.role,
    email: detail.email,
    city: detail.city,
    phone: detail.phone,
    status: detail.status,
    quality: detail.quality,
    skills: detail.skills,
    hobbies: detail.hobbies,
    height_cm: detail.heightCm,
    weight_kg: detail.weightKg,
    available_in_days: detail.availableInDays,
    project_summary: detail.projectSummary,
    projects: detail.projects.map((project) => ({
      project_id: project.projectId,
      name: project.name,
      role: project.role,
      summary: project.summary,
      tech_stack: project.techStack,
      responsibilities: project.responsibilities,
      achievements: project.achievements,
      metrics: project.metrics,
      source_pages: project.sourcePages,
      confidence: project.confidence
    })),
    analysis: {
      focus_topics: detail.analysis.focusTopics,
      strengths: detail.analysis.strengths,
      risks: detail.analysis.risks,
      recommended_languages: detail.analysis.recommendedLanguages,
      missing_fields: detail.analysis.missingFields
    },
    processing: detail.processing,
    review_notes: detail.reviewNotes,
    parse_metrics: {
      first_page_characters: detail.parseMetrics.firstPageCharacters,
      multimodal_pages: detail.parseMetrics.multimodalPages,
      confidence: detail.parseMetrics.confidence
    },
    paper_id: detail.paperId,
    invitation_token: detail.invitationToken,
    result_id: detail.resultId
  };
}

describe("CandidateEditView", () => {
  beforeEach(() => {
    mocks.loadCandidateDetail.mockReset();
    mocks.updateCandidateDetail.mockReset();
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    Object.defineProperty(window, "localStorage", {
      value: createStorageMock(),
      configurable: true
    });
    window.localStorage.clear();
  });

  it("shows a loading state, then merges the local draft into the edit workspace", async () => {
    const request = createDeferred<CandidateDetail>();
    mocks.loadCandidateDetail.mockReturnValueOnce(request.promise);
    window.localStorage.setItem(
      "admin-candidate-draft:candidate-1",
      JSON.stringify({
        name: "陈晓（草稿）",
        skills: ["TypeScript", "Node.js"],
        reviewNotes: ["草稿备注 1", "草稿备注 2"],
        availableInDays: 7
      })
    );

    const { wrapper } = await mountView();

    expect(wrapper.text()).toContain("正在加载候选人画像");
    expect(wrapper.text()).not.toContain("编辑页会先读取候选人详情");

    request.resolve(buildCandidateDetail());
    await flushPromises();
    await nextTick();

    expect(wrapper.find(".edit-page__layout").exists()).toBe(true);
    expect(wrapper.text()).toContain("基本信息");
    expect(wrapper.text()).toContain("结构化档案");
    expect(wrapper.text()).toContain("复核备注");
    expect(wrapper.text()).not.toContain("直接覆盖本地草稿");
    expect(wrapper.text()).not.toContain("保存优先写后端，失败时自动落本地草稿");
    expect(fieldValue(wrapper, 'input[name="name"]')).toBe("陈晓（草稿）");
    expect(fieldValue(wrapper, 'input[name="skillsText"]')).toBe("TypeScript, Node.js");
    expect(fieldValue(wrapper, 'input[name="availableInDaysText"]')).toBe("7");
    expect(fieldValue(wrapper, 'textarea[name="reviewNotesText"]')).toBe("草稿备注 1\n草稿备注 2");
  });

  it("saves to the backend, clears the local draft, and shows the synced state on success", async () => {
    window.localStorage.setItem(
      "admin-candidate-draft:candidate-1",
      JSON.stringify({
        name: "旧草稿"
      })
    );
    mocks.loadCandidateDetail.mockResolvedValue(buildCandidateDetail());
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () =>
        buildCandidateApiResponse({
          name: "陈晓（已保存）",
          skills: ["TypeScript", "Node.js"],
          reviewNotes: ["已同步备注"]
        })
    });

    const { wrapper } = await mountView();

    await flushPromises();
    await nextTick();

    await wrapper.get('input[name="name"]').setValue("陈晓（已保存）");
    await wrapper.get('input[name="skillsText"]').setValue("TypeScript, Node.js");
    await wrapper.get('textarea[name="reviewNotesText"]').setValue("已同步备注");
    await wrapper.get('button[data-testid="save-profile"]').trigger("click");
    await flushPromises();
    await nextTick();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/admin/candidates/candidate-1",
      expect.objectContaining({
        method: "PUT",
        headers: { "Content-Type": "application/json" }
      })
    );
    expect(JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body))).toMatchObject({
      name: "陈晓（已保存）",
      skills: ["TypeScript", "Node.js"],
      review_notes: ["已同步备注"]
    });
    expect(window.localStorage.getItem("admin-candidate-draft:candidate-1")).toBeNull();
    expect(wrapper.text()).toContain("画像已同步到后端");
    expect(fieldValue(wrapper, 'input[name="name"]')).toBe("陈晓（已保存）");
    expect(fieldValue(wrapper, 'input[name="skillsText"]')).toBe("TypeScript, Node.js");
    expect(fieldValue(wrapper, 'textarea[name="reviewNotesText"]')).toBe("已同步备注");
  });

  it("falls back to local storage and shows the draft save state when backend save fails", async () => {
    mocks.loadCandidateDetail.mockResolvedValue(buildCandidateDetail());
    fetchMock.mockRejectedValue(new Error("network"));

    const { wrapper } = await mountView();

    await flushPromises();
    await nextTick();

    await wrapper.get('input[name="name"]').setValue("陈晓（本地草稿）");
    await wrapper.get('input[name="skillsText"]').setValue("TypeScript, Prompt Design");
    await wrapper.get('textarea[name="reviewNotesText"]').setValue("本地备注一\n本地备注二");
    await wrapper.get('button[data-testid="save-profile"]').trigger("click");
    await flushPromises();
    await nextTick();

    expect(JSON.parse(window.localStorage.getItem("admin-candidate-draft:candidate-1") || "{}")).toMatchObject({
      name: "陈晓（本地草稿）",
      skills: ["TypeScript", "Prompt Design"],
      reviewNotes: ["本地备注一", "本地备注二"]
    });
    expect(wrapper.text()).toContain("本地草稿已保存");
  });

  it("ignores a stale save completion after navigating to another candidate", async () => {
    const saveRequest = createDeferred<{
      ok: boolean;
      json: () => Promise<CandidateApiResponse>;
    }>();
    mocks.loadCandidateDetail
      .mockResolvedValueOnce(buildCandidateDetail())
      .mockResolvedValueOnce(
        buildCandidateDetail({
          id: "candidate-2",
          taskId: "task-2",
          name: "李雷",
          role: "后端工程师",
          email: "li@example.com",
          city: "杭州",
          phone: "13900000000",
          paperId: "paper-2"
        })
      );
    fetchMock.mockReturnValueOnce(saveRequest.promise);
    window.localStorage.setItem("admin-candidate-draft:candidate-1", JSON.stringify({ name: "候选人 A 草稿" }));
    window.localStorage.setItem("admin-candidate-draft:candidate-2", JSON.stringify({ name: "候选人 B 草稿" }));

    const { wrapper, router } = await mountView();

    await flushPromises();
    await nextTick();

    await wrapper.get('input[name="name"]').setValue("陈晓（保存中）");
    await wrapper.get('button[data-testid="save-profile"]').trigger("click");

    await router.push("/admin/candidates/candidate-2/edit");
    await flushPromises();
    await nextTick();

    expect(fieldValue(wrapper, 'input[name="name"]')).toBe("候选人 B 草稿");

    saveRequest.resolve({
      ok: true,
      json: async () =>
        buildCandidateApiResponse({
          name: "陈晓（已保存）",
          skills: ["TypeScript", "Node.js"]
        })
    });
    await flushPromises();
    await nextTick();

    expect(fieldValue(wrapper, 'input[name="name"]')).toBe("候选人 B 草稿");
    expect(window.localStorage.getItem("admin-candidate-draft:candidate-1")).toBe(
      JSON.stringify({ name: "候选人 A 草稿" })
    );
    expect(window.localStorage.getItem("admin-candidate-draft:candidate-2")).toBe(
      JSON.stringify({ name: "候选人 B 草稿" })
    );
    expect(wrapper.text()).not.toContain("画像已同步到后端");
  });

  it("preserves the original candidate draft when a stale save fails after navigation", async () => {
    const saveRequest = createDeferred<{
      ok: boolean;
      json: () => Promise<CandidateApiResponse>;
    }>();
    mocks.loadCandidateDetail
      .mockResolvedValueOnce(buildCandidateDetail())
      .mockResolvedValueOnce(
        buildCandidateDetail({
          id: "candidate-2",
          taskId: "task-2",
          name: "李雷",
          role: "后端工程师",
          email: "li@example.com",
          city: "杭州",
          phone: "13900000000",
          paperId: "paper-2"
        })
      );
    fetchMock.mockReturnValueOnce(saveRequest.promise);
    window.localStorage.setItem("admin-candidate-draft:candidate-2", JSON.stringify({ name: "候选人 B 草稿" }));

    const { wrapper, router } = await mountView();

    await flushPromises();
    await nextTick();

    await wrapper.get('input[name="name"]').setValue("陈晓（失败待保留）");
    await wrapper.get('textarea[name="reviewNotesText"]').setValue("失败后保留到本地");
    await wrapper.get('button[data-testid="save-profile"]').trigger("click");

    await router.push("/admin/candidates/candidate-2/edit");
    await flushPromises();
    await nextTick();

    saveRequest.reject(new Error("network"));
    await flushPromises();
    await nextTick();

    expect(JSON.parse(window.localStorage.getItem("admin-candidate-draft:candidate-1") || "{}")).toMatchObject({
      name: "陈晓（失败待保留）",
      reviewNotes: ["失败后保留到本地"]
    });
    expect(window.localStorage.getItem("admin-candidate-draft:candidate-2")).toBe(
      JSON.stringify({ name: "候选人 B 草稿" })
    );
    expect(fieldValue(wrapper, 'input[name="name"]')).toBe("候选人 B 草稿");
    expect(wrapper.text()).not.toContain("本地草稿已保存");
  });

  it("treats a successful PUT as saved even when the gateway refresh abstraction would fail", async () => {
    window.localStorage.setItem("admin-candidate-draft:candidate-1", JSON.stringify({ name: "旧草稿" }));
    mocks.loadCandidateDetail.mockResolvedValue(buildCandidateDetail());
    mocks.updateCandidateDetail.mockRejectedValue(new Error("refresh failed"));
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () =>
        buildCandidateApiResponse({
          name: "陈晓（PUT 成功）",
          skills: ["TypeScript", "Prompt Design"],
          reviewNotes: ["后端已保存"]
        })
    });

    const { wrapper } = await mountView();

    await flushPromises();
    await nextTick();

    await wrapper.get('input[name="name"]').setValue("陈晓（PUT 成功）");
    await wrapper.get('input[name="skillsText"]').setValue("TypeScript, Prompt Design");
    await wrapper.get('textarea[name="reviewNotesText"]').setValue("后端已保存");
    await wrapper.get('button[data-testid="save-profile"]').trigger("click");
    await flushPromises();
    await nextTick();

    expect(window.localStorage.getItem("admin-candidate-draft:candidate-1")).toBeNull();
    expect(wrapper.text()).toContain("画像已同步到后端");
    expect(wrapper.text()).not.toContain("本地草稿已保存");
    expect(fieldValue(wrapper, 'input[name="name"]')).toBe("陈晓（PUT 成功）");
    expect(fieldValue(wrapper, 'input[name="skillsText"]')).toBe("TypeScript, Prompt Design");
    expect(mocks.updateCandidateDetail).not.toHaveBeenCalled();
  });
});
