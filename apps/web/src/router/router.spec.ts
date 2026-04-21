import { describe, expect, it } from "vitest";

import { routes } from "./index";

describe("router", () => {
  it("includes the admin candidate list route", () => {
    expect(routes.some((route) => route.path === "/admin/candidates")).toBe(true);
  });
});
