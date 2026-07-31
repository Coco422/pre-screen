import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  restore: vi.fn(async () => {}),
  session: { isLoggedIn: false }
}));

vi.mock("../stores/adminSession", () => ({
  useAdminSessionStore: () => ({
    restore: mocks.restore,
    isLoggedIn: mocks.session.isLoggedIn
  })
}));

import { createAppRouter, routes } from "./index";

describe("router", () => {
  beforeEach(() => {
    mocks.restore.mockReset();
    mocks.restore.mockResolvedValue(undefined);
    mocks.session.isLoggedIn = false;
  });

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
    expect(childPaths).toContain("monitor");
    expect(childPaths).toContain("settings");
  });

  it("includes the exam route trilogy", () => {
    expect(routes.some((route) => route.path === "/exam/:token")).toBe(true);
    expect(routes.some((route) => route.path === "/exam/:token/start")).toBe(true);
    expect(routes.some((route) => route.path === "/exam/:token/session")).toBe(true);
    expect(routes.some((route) => route.path === "/exam/:token/submitted")).toBe(true);
  });

  it("redirects unauthenticated users from admin pages to login", async () => {
    const router = createAppRouter();

    await router.push("/admin/dashboard");

    expect(mocks.restore).toHaveBeenCalled();
    expect(router.currentRoute.value.fullPath).toBe("/login");
  });

  it("sends authenticated users from login to the new dashboard path", async () => {
    const router = createAppRouter();
    mocks.session.isLoggedIn = true;

    await router.push("/login");

    expect(router.currentRoute.value.fullPath).toBe("/admin/dashboard");
  });
});
