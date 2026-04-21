<template>
  <div class="shell-page login-page">
    <section class="login-layout">
      <article class="glass-card login-story">
        <div class="pill">HR Login</div>
        <h1 class="login-title">登录后，今天的待办会直接展开给你</h1>
        <p class="section-copy">后台会先帮你对齐招聘筛选的主流程：创建任务、上传简历、发卷跟进、查看结果，不用再自己找入口。</p>

        <div class="story-metrics">
          <article class="metric-tile">
            <div class="metric-value">1</div>
            <div class="metric-label">先登录验证身份</div>
          </article>
          <article class="metric-tile">
            <div class="metric-value">2</div>
            <div class="metric-label">查看今日待办</div>
          </article>
          <article class="metric-tile">
            <div class="metric-value">3</div>
            <div class="metric-label">沿着下一步继续处理</div>
          </article>
        </div>

        <div class="story-steps">
          <article
            v-for="(step, index) in workflowSteps"
            :key="step.title"
            class="story-step"
            :class="{ 'story-step--active': index <= completedStepIndex }"
          >
            <div class="story-step__index">0{{ index + 1 }}</div>
            <div class="story-step__body">
              <strong>{{ step.title }}</strong>
              <span>{{ step.copy }}</span>
            </div>
          </article>
        </div>
      </article>

      <section class="glass-card login-card">
        <div class="pill">Access</div>
        <h2 class="section-title">登录招聘筛选后台</h2>
        <p class="section-copy">输入账号后，系统会验证身份、同步工作台摘要，并带你进入最需要先处理的页面。</p>

        <form class="login-form" @submit.prevent="submit">
          <label class="field">
            <span>账号</span>
            <input v-model="username" class="soft-input" placeholder="hr-demo" :disabled="submitting" />
          </label>
          <label class="field">
            <span>密码</span>
            <input v-model="password" class="soft-input" type="password" placeholder="demo-pass" :disabled="submitting" />
          </label>

          <div class="login-hint">
            <strong>默认演示账号</strong>
            <span>`hr-demo / demo-pass`</span>
          </div>

          <div class="login-feedback" :class="{ 'login-feedback--active': submitting, 'login-feedback--error': Boolean(errorMessage) }">
            <strong>{{ feedbackTitle }}</strong>
            <span>{{ feedbackCopy }}</span>
          </div>

          <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>

          <button class="primary-btn login-btn" type="submit" :disabled="submitting">
            {{ submitting ? "正在登录并同步工作台..." : "进入工作台" }}
          </button>
        </form>
      </section>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from "vue";
import { useRouter } from "vue-router";

import { useAdminSessionStore } from "../../stores/adminSession";

const router = useRouter();
const sessionStore = useAdminSessionStore();
const username = ref("hr-demo");
const password = ref("demo-pass");
const submitting = ref(false);
const errorMessage = ref("");
const progressStepIndex = ref(-1);

const workflowSteps = [
  { title: "验证 HR 账号", copy: "确认当前登录人身份和访问权限。" },
  { title: "同步今日工作台", copy: "准备任务、候选人和结果摘要。" },
  { title: "进入下一步", copy: "把你带到工作台，继续今天最该先做的事。" }
];

let progressTimer: number | undefined;

const completedStepIndex = computed(() => Math.max(progressStepIndex.value, 0));
const feedbackTitle = computed(() => {
  if (errorMessage.value) {
    return "登录没有成功";
  }
  if (submitting.value) {
    return workflowSteps[Math.min(progressStepIndex.value, workflowSteps.length - 1)]?.title ?? "正在登录";
  }
  return "登录后会发生什么";
});
const feedbackCopy = computed(() => {
  if (errorMessage.value) {
    return "请检查账号密码，或稍后重试。登录成功后你会直接看到今日待办和建议下一步。";
  }
  if (submitting.value) {
    return workflowSteps[Math.min(progressStepIndex.value, workflowSteps.length - 1)]?.copy ?? "系统正在为你准备工作台。";
  }
  return "系统会先验证账号，再同步工作台摘要，最后把你送到今天的筛选工作入口。";
});

function startProgressFeedback() {
  window.clearInterval(progressTimer);
  progressStepIndex.value = 0;
  progressTimer = window.setInterval(() => {
    progressStepIndex.value = Math.min(progressStepIndex.value + 1, workflowSteps.length - 1);
  }, 700);
}

function stopProgressFeedback() {
  window.clearInterval(progressTimer);
}

async function submit() {
  submitting.value = true;
  errorMessage.value = "";
  startProgressFeedback();

  try {
    await sessionStore.signIn(username.value.trim(), password.value.trim());
    progressStepIndex.value = workflowSteps.length - 1;
    await router.replace("/admin");
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "登录失败，请稍后重试。";
  } finally {
    submitting.value = false;
    stopProgressFeedback();
  }
}

onBeforeUnmount(() => {
  stopProgressFeedback();
});
</script>

<style scoped>
.login-page {
  display: grid;
  place-items: center;
}

.login-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(360px, 0.8fr);
  gap: 24px;
  width: min(1080px, 100%);
}

.login-story,
.login-card {
  padding: 32px;
}

.login-title {
  margin: 18px 0 0;
  font-size: clamp(2.2rem, 4vw, 3.4rem);
  line-height: 0.98;
  letter-spacing: -0.05em;
}

.story-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-top: 24px;
}

.story-steps {
  display: grid;
  gap: 14px;
  margin-top: 24px;
}

.story-step {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 14px;
  align-items: start;
  padding: 16px;
  border-radius: 20px;
  background: rgba(20, 33, 61, 0.04);
  border: 1px solid rgba(20, 33, 61, 0.06);
}

.story-step--active {
  background: rgba(15, 118, 110, 0.08);
  border-color: rgba(15, 118, 110, 0.14);
}

.story-step__index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 48px;
  height: 48px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.9);
  font-weight: 700;
}

.story-step__body {
  display: grid;
  gap: 6px;
  color: var(--ink-soft);
  line-height: 1.6;
}

.login-form {
  display: grid;
  gap: 16px;
  margin-top: 24px;
}

.field {
  display: grid;
  gap: 8px;
  color: var(--ink-soft);
}

.login-hint,
.login-feedback {
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.05);
  color: var(--ink-soft);
}

.login-feedback--active {
  background: rgba(15, 118, 110, 0.12);
  color: var(--accent-strong);
}

.login-feedback--error {
  background: rgba(220, 38, 38, 0.1);
  color: var(--danger);
}

.error-banner {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(220, 38, 38, 0.1);
  color: var(--danger);
}

.login-btn {
  width: 100%;
  justify-content: center;
}

@media (max-width: 960px) {
  .login-layout,
  .story-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
