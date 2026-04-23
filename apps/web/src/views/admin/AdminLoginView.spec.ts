import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AdminLoginView from "./AdminLoginView.vue";

const mocks = vi.hoisted(() => ({
  routerReplace: vi.fn(),
  signIn: vi.fn(async () => ({ sessionToken: "token" }))
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({
    replace: mocks.routerReplace
  })
}));

vi.mock("../../stores/adminSession", () => ({
  useAdminSessionStore: () => ({
    signIn: mocks.signIn
  })
}));

const inputStub = {
  props: ["modelValue", "name", "autocomplete", "type", "placeholder", "disabled"],
  emits: ["update:modelValue"],
  template:
    "<input :name=\"name\" :autocomplete=\"autocomplete\" :type=\"type || 'text'\" :placeholder=\"placeholder\" :disabled=\"disabled\" :value=\"modelValue\" @input=\"$emit('update:modelValue', $event.target.value)\" />"
};

describe("AdminLoginView", () => {
  beforeEach(() => {
    mocks.routerReplace.mockReset();
    mocks.signIn.mockClear();
  });

  it("renders a minimal login form for hr sign-in", async () => {
    const wrapper = mount(AdminLoginView, {
      global: {
        stubs: {
          ElInput: inputStub,
          ElAlert: true,
          ElButton: { template: "<button type='submit'><slot /></button>" }
        }
      }
    });

    await nextTick();

    expect(wrapper.find(".login-screen").exists()).toBe(true);
    expect(wrapper.get('input[name="username"]').attributes("autocomplete")).toBe("username");
    expect(wrapper.get('input[name="password"]').attributes("autocomplete")).toBe("current-password");
    expect(wrapper.text()).toContain("Pre-Screen");
    expect(wrapper.text()).toContain("HR 登录");
    expect(wrapper.text()).toContain("招聘初筛控制台");
    expect(wrapper.text()).not.toContain("记住账号");
    expect(wrapper.text()).not.toContain("忘记密码");
  });

  it("submits the form and redirects to the dashboard", async () => {
    const wrapper = mount(AdminLoginView, {
      global: {
        stubs: {
          ElInput: inputStub,
          ElAlert: true,
          ElButton: { template: "<button type='submit'><slot /></button>" }
        }
      }
    });

    await wrapper.get('input[name="username"]').setValue("hr-demo");
    await wrapper.get('input[name="password"]').setValue("demo-pass");
    await wrapper.get("form").trigger("submit.prevent");

    expect(mocks.signIn).toHaveBeenCalledWith("hr-demo", "demo-pass");
    expect(mocks.routerReplace).toHaveBeenCalledWith("/admin/dashboard");
  });
});
