import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  fetchAdminSession,
  loadTasks,
  loginAdmin
} from "./gateway";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

describe("gateway fail-closed behavior", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("loginAdmin rejects on network failure instead of returning a demo session", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    }));

    await expect(loginAdmin("hr-demo", "demo-pass")).rejects.toMatchObject({
      name: "ApiError",
      status: null
    });
  });

  it("loginAdmin propagates HTTP 401 with server detail", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      jsonResponse({ detail: "账号或密码错误" }, 401)
    ));

    await expect(loginAdmin("hr-demo", "wrong")).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      detail: "账号或密码错误"
    });
  });

  it("loginAdmin rejects success payloads that lack a session token", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      jsonResponse({ user_name: "Ray HR", role: "HR" })
    ));

    await expect(loginAdmin("hr-demo", "demo-pass")).rejects.toBeInstanceOf(ApiError);
  });

  it("fetchAdminSession rejects responses without required user fields", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      jsonResponse({ session_token: "token-only" })
    ));

    await expect(fetchAdminSession()).rejects.toBeInstanceOf(ApiError);
  });

  it("loadTasks propagates list failures instead of returning an empty array", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      jsonResponse({ detail: "服务暂不可用" }, 503)
    ));

    await expect(loadTasks()).rejects.toMatchObject({
      name: "ApiError",
      status: 503,
      detail: "服务暂不可用"
    });
  });
});
