import { describe, expect, it } from "vitest";

import { routes } from "./index";

describe("router", () => {
  it("redirects the root route to login", () => {
    const rootRoute = routes.find((route) => route.path === "/");

    expect(rootRoute?.redirect).toBe("/login");
  });

  it("includes the login route", () => {
    expect(routes.some((route) => route.path === "/login")).toBe(true);
  });

  it("includes the admin workbench route", () => {
    expect(routes.some((route) => route.path === "/admin")).toBe(true);
  });

  it("includes the task creation route", () => {
    expect(routes.some((route) => route.path === "/admin/tasks/new")).toBe(true);
  });

  it("includes the admin candidate list route", () => {
    expect(routes.some((route) => route.path === "/admin/candidates")).toBe(true);
  });

  it("includes the candidate edit route", () => {
    expect(routes.some((route) => route.path === "/admin/candidates/:candidateId/edit")).toBe(true);
  });

  it("includes the result list route", () => {
    expect(routes.some((route) => route.path === "/admin/results")).toBe(true);
  });
});
