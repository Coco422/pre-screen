<template>
  <div class="login-screen">
    <div class="login-brand">
      <h1>Pre-Screen</h1>
      <p>技术招聘智能筛选系统</p>
    </div>

    <section class="login-card">
      <!-- tabs -->
      <div class="login-tabs" role="tablist">
        <button
          role="tab"
          :class="['login-tab', { 'login-tab--active': loginType === 'hr' }]"
          @click="loginType = 'hr'"
        >HR 登录</button>
        <button
          role="tab"
          :class="['login-tab', { 'login-tab--active': loginType === 'candidate' }]"
          @click="loginType = 'candidate'"
        >候选人登录</button>
      </div>

      <form class="login-form" @submit.prevent="submit">
        <Transition name="login-fade" mode="out-in">
          <div :key="loginType" class="login-form__fields">
            <label>
              <span>账号</span>
              <el-input
                v-model="username"
                name="username"
                autocomplete="username"
                placeholder="请输入账号"
                :disabled="submitting"
              />
            </label>

            <label>
              <span>密码</span>
              <el-input
                v-model="password"
                name="password"
                type="password"
                show-password
                autocomplete="current-password"
                placeholder="请输入密码"
                :disabled="submitting"
              />
            </label>

            <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" />

            <div class="login-form__meta">
              <el-checkbox v-model="rememberMe">记住密码</el-checkbox>
              <button type="button" class="login-form__forgot">忘记密码?</button>
            </div>
          </div>
        </Transition>

        <el-button class="login-form__submit" type="primary" native-type="submit" :loading="submitting">
          登录
        </el-button>
      </form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";

import { useAdminSessionStore } from "../../stores/adminSession";

const router = useRouter();
const sessionStore = useAdminSessionStore();
const loginType = ref<"hr" | "candidate">("hr");
const username = ref("hr-demo");
const password = ref("demo-pass");
const rememberMe = ref(false);
const submitting = ref(false);
const errorMessage = ref("");

async function submit() {
  submitting.value = true;
  errorMessage.value = "";

  try {
    if (loginType.value === "hr") {
      await sessionStore.signIn(username.value.trim(), password.value.trim());
      await router.replace("/admin/dashboard");
    } else {
      // TODO: candidate login
    }
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
}

</script>

<style scoped>
.login-screen {
  position: relative;
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(300px, 368px);
  align-items: center;
  min-height: 100vh;
  overflow: hidden;
  padding: 80px clamp(32px, 8vw, 120px);
  background: #f6faff url("../../public/image/bg.png") center / cover no-repeat;
}

.login-brand {
  position: relative;
  z-index: 1;
  align-self: center;
  margin-top: -474px;
  margin-left: 20px;
}

.login-brand h1 {
  margin: 0;
  color: #10306b;
  font-size: clamp(40px, 4.7vw, 62px);
  font-weight: 600;
  line-height: 1.08;
  letter-spacing: 0;
}

.login-brand p {
  margin: 18px 0 0;
  color: #4c6385;
  font-size: clamp(18px, 1.6vw, 24px);
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: 0;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: 28px 32px 30px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(210, 224, 244, 0.78);
  border-radius: 8px;
  box-shadow:
    0 0 0 1px rgba(221, 232, 246, 0.48),
    0 4px 14px rgba(22, 49, 93, 0.08);
  backdrop-filter: blur(10px);
}

.login-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 22px;
}

.login-tab {
  position: relative;
  min-height: 34px;
  border: 0;
  background: transparent;
  color: #7a8aa5;
  cursor: pointer;
  font-size: 14px;
  font-weight: 700;
}

.login-tab::after {
  position: absolute;
  right: 18%;
  bottom: 0;
  left: 18%;
  height: 3px;
  content: "";
  background: transparent;
  border-radius: 999px;
}

.login-tab--active {
  color: #2f6cf6;
}

.login-tab--active::after {
  background: #2f6cf6;
}

.login-form,
.login-form__fields {
  display: grid;
  gap: 18px;
}

.login-form label {
  display: grid;
  gap: 8px;
  color: #526075;
  font-size: 14px;
  font-weight: 700;
}

.login-form :deep(.el-input__wrapper) {
  min-height: 44px;
  border-radius: 4px;
  box-shadow: 0 0 0 1px #dde6f2 inset;
}

.login-form__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: -2px;
  white-space: nowrap;
}

.login-form__meta :deep(.el-checkbox) {
  display: inline-flex;
  align-items: center;
  height: auto;
  margin-right: 0;
  color: #536781;
  font-weight: 500;
}

.login-form__meta :deep(.el-checkbox__input) {
  display: inline-flex;
  align-items: center;
}

.login-form__meta :deep(.el-checkbox__label) {
  display: inline-flex;
  align-items: center;
  padding-left: 6px;
  font-size: 13px;
  line-height: 14px;
}

.login-form__forgot {
  border: 0;
  padding: 0;
  background: transparent;
  color: #2f6cf6;
  cursor: pointer;
  font-size: 13px;
  font-weight: 700;
  white-space: nowrap;
}

.login-form__submit {
  width: 100%;
  min-height: 42px;
  margin-top: 10px;
  border-radius: 4px;
  font-size: 15px;
  font-weight: 700;
}

.login-fade-enter-active,
.login-fade-leave-active {
  transition: opacity 140ms ease, transform 140ms ease;
}

.login-fade-enter-from,
.login-fade-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

@media (max-width: 760px) {
  .login-screen {
    grid-template-columns: 1fr;
    align-content: center;
    gap: 36px;
    padding: 48px 22px;
  }

  .login-brand {
    margin-top: -200px;
    text-align: left;
  }

  .login-card {
    padding: 24px 20px 26px;
  }
}
</style>
