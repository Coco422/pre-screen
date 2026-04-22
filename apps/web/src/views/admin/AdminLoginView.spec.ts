import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AdminLoginView from "./AdminLoginView.vue";

const mocks = vi.hoisted(() => ({
  messageInfo: vi.fn()
}));

vi.mock("element-plus", () => ({
  ElMessage: {
    info: mocks.messageInfo
  }
}));

vi.mock("vue-router", () => ({
  useRouter: () => ({
    replace: vi.fn()
  })
}));

vi.mock("../../stores/adminSession", () => ({
  useAdminSessionStore: () => ({
    signIn: vi.fn(async () => ({ sessionToken: "token" }))
  })
}));

const STORAGE_KEY = "pre-screen:admin-login-username";

const inputStub = {
  props: ["modelValue", "name", "autocomplete", "type", "placeholder", "disabled"],
  emits: ["update:modelValue"],
  template:
    "<input :name=\"name\" :autocomplete=\"autocomplete\" :type=\"type || 'text'\" :placeholder=\"placeholder\" :disabled=\"disabled\" :value=\"modelValue\" @input=\"$emit('update:modelValue', $event.target.value)\" />"
};

const checkboxStub = {
  props: ["modelValue"],
  emits: ["update:modelValue"],
  template:
    "<label><input type=\"checkbox\" :checked=\"modelValue\" @change=\"$emit('update:modelValue', $event.target.checked)\" /><slot /></label>"
};

describe("AdminLoginView", () => {
  beforeEach(() => {
    window.localStorage.clear();
    mocks.messageInfo.mockReset();
  });

  it("restores the remembered username, exposes autofill metadata, and shows reset guidance", async () => {
    window.localStorage.setItem(STORAGE_KEY, "alice");

    const wrapper = mount(AdminLoginView, {
      global: {
        stubs: {
          ElInput: inputStub,
          ElCheckbox: checkboxStub,
          ElAlert: true,
          ElButton: { template: "<button type='submit'><slot /></button>" }
        }
      }
    });

    await nextTick();

    expect(wrapper.find(".login-screen__brand").exists()).toBe(true);
    expect(wrapper.find(".login-card").exists()).toBe(true);
    expect(wrapper.get('input[name="username"]').attributes("autocomplete")).toBe("username");
    expect(wrapper.get('input[name="username"]').element).toHaveProperty("value", "alice");
    expect(wrapper.get('input[name="password"]').attributes("autocomplete")).toBe("current-password");
    expect(wrapper.get('input[type="checkbox"]').element).toHaveProperty("checked", true);
    expect(wrapper.text()).toContain("Pre-Screen");
    expect(wrapper.text()).toContain("HR 登录");
    expect(wrapper.text()).toContain("技术招聘智能筛选系统");
    expect(wrapper.text()).not.toContain("候选人登录");
    expect(wrapper.get('button[type="button"]').text()).toContain("忘记密码?");

    await wrapper.get('button[type="button"]').trigger("click");

    expect(mocks.messageInfo).toHaveBeenCalledWith("请联系管理员重置密码。");
  });

  it("persists and clears the remembered username when the checkbox changes", async () => {
    const wrapper = mount(AdminLoginView, {
      global: {
        stubs: {
          ElInput: inputStub,
          ElCheckbox: checkboxStub,
          ElAlert: true,
          ElButton: { template: "<button type='submit'><slot /></button>" }
        }
      }
    });

    await wrapper.get('input[name="username"]').setValue("new-admin");
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();

    await wrapper.get('input[type="checkbox"]').setValue(true);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("new-admin");

    await wrapper.get('input[type="checkbox"]').setValue(false);
    expect(window.localStorage.getItem(STORAGE_KEY)).toBeNull();
  });
});
