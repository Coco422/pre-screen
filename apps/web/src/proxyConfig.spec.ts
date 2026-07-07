// @vitest-environment node

import { describe, expect, it } from "vitest";

import config from "../vite.config";

describe("vite proxy config", () => {
  it("rewrites api requests to the gateway root path", () => {
    const proxy = config.server?.proxy?.["/api"];

    expect(proxy).toBeTruthy();
    if (!proxy || typeof proxy === "string") {
      throw new Error("api proxy config is missing");
    }

    expect(proxy.rewrite?.("/api/admin/dashboard")).toBe("/admin/dashboard");
  });
});
