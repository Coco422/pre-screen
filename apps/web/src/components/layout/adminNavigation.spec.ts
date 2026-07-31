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
      "考试监控",
      "系统设置"
    ]);
  });

  it("contains no placeholder destinations", () => {
    const placeholderItems = adminNavigation.filter((item) => item.placeholder);

    expect(placeholderItems).toEqual([]);
  });
});
