import { describe, expect, it } from "vitest";

import { buildCandidateEditPath, buildPaperRouteTarget, buildTaskCreatePath } from "./adminRouting";

describe("admin routing helpers", () => {
  it("builds the candidate edit path from the active candidate id", () => {
    expect(buildCandidateEditPath("c-042")).toBe("/admin/candidates/c-042/edit");
  });

  it("reuses the paper id from backend actions and binds the current candidate to the query", () => {
    expect(
      buildPaperRouteTarget("c-042", [{ label: "生成考卷草稿", target: "/admin/papers/p-204?from=detail" }])
    ).toEqual({
      path: "/admin/papers/p-204",
      query: {
        candidateId: "c-042"
      }
    });
  });

  it("falls back to the default paper route when backend actions are missing", () => {
    expect(buildPaperRouteTarget("c-042", [])).toEqual({
      path: "/admin/papers/new",
      query: {
        candidateId: "c-042"
      }
    });
  });

  it("builds the task create route", () => {
    expect(buildTaskCreatePath()).toBe("/admin/tasks/new");
  });
});
