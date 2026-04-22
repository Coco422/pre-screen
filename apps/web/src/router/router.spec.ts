import { describe, expect, it } from "vitest";

import { routes } from "./index";

describe("router", () => {
  it("redirects the root route to login", () => {
    const rootRoute = routes.find((route) => route.path === "/");

    expect(rootRoute?.redirect).toBe("/login");
  });

  it("includes the admin dashboard route", () => {
    expect(routes.some((route) => route.path === "/admin")).toBe(true);
    const adminRoute = routes.find((route) => route.path === "/admin");

    const childPaths = Array.isArray(adminRoute?.children)
      ? adminRoute.children.map((route) => route.path)
      : [];

    expect(adminRoute?.children?.some((route) => route.name === "admin-workbench")).toBe(true);
    expect(childPaths).toContain("dashboard");
    expect(childPaths).toContain("workbench");
    expect(childPaths).toContain("tasks");
    expect(childPaths).toContain("candidates");
    expect(childPaths).toContain("papers");
    expect(childPaths).toContain("results");
    expect(childPaths).toContain("risk");
    expect(childPaths).toContain("settings");
  });

  it("includes the exam route trilogy", () => {
    expect(routes.some((route) => route.path === "/exam/:token")).toBe(true);
    expect(routes.some((route) => route.path === "/exam/:token/start")).toBe(true);
    expect(routes.some((route) => route.path === "/exam/:token/session")).toBe(true);
    expect(routes.some((route) => route.path === "/exam/:token/submitted")).toBe(true);
  });
});
