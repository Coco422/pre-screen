<template>
  <div class="login-screen">
    <section class="login-screen__brand">
      <div class="login-screen__copy">
        <h1>Pre-Screen</h1>
        <p>招聘初筛控制台</p>
      </div>

      <div class="login-hero" aria-hidden="true">
        <div class="login-hero__grid"></div>
        <div class="login-hero__shield">
          <span></span>
        </div>
      </div>
    </section>

    <section class="login-card">
      <header class="login-card__header">
        <h2>HR 登录</h2>
        <p>进入工作台</p>
      </header>

      <form class="login-form" @submit.prevent="submit">
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
const username = ref("hr-demo");
const password = ref("demo-pass");
const submitting = ref(false);
const errorMessage = ref("");

async function submit() {
  submitting.value = true;
  errorMessage.value = "";

  try {
    await sessionStore.signIn(username.value.trim(), password.value.trim());
    await router.replace("/admin/dashboard");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
}
</script>
