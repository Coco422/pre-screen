import { describe, expect, it } from "vitest";

import { adminNavigation } from "./adminNavigation";

describe("adminNavigation", () => {
  it("defines the approved primary navigation", () => {
    expect(adminNavigation.map((item) => item.label)).toEqual([
      "工作台",
      "任务中心",
      "候选人",
      "考卷管理",
      "结果中心",
      "风险管理",
      "系统设置"
    ]);
  });

  it("marks the placeholder destinations that are not implemented in phase one", () => {
    const placeholderItems = adminNavigation.filter((item) => item.placeholder);

    expect(placeholderItems.map((item) => item.label)).toEqual([
      "考卷管理",
      "风险管理",
      "系统设置"
    ]);
  });
});
