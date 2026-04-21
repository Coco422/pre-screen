<template>
  <section class="glass-card task-create-card">
    <div class="page-head">
      <div>
        <div class="pill">New Task</div>
        <h2 class="section-title page-title">新建筛选任务</h2>
      </div>
      <RouterLink class="secondary-btn" :to="{ name: 'admin-workbench' }">返回工作台</RouterLink>
    </div>

    <div class="form-grid">
      <label class="field">
        <span>任务名称</span>
        <input v-model="form.title" class="soft-input" placeholder="例如：前端开发工程师第一轮筛选" />
      </label>
      <label class="field">
        <span>岗位名称</span>
        <input v-model="form.role" class="soft-input" placeholder="前端开发工程师" />
      </label>
      <label class="field">
        <span>考卷模板</span>
        <input v-model="form.templateName" class="soft-input" placeholder="前端通用模板" />
      </label>
      <label class="field field--full">
        <span>JD 描述</span>
        <textarea
          v-model="form.jdText"
          class="soft-input soft-textarea"
          rows="8"
          placeholder="写清楚技能要求、岗位职责和重点考察方向。"
        />
      </label>
    </div>

    <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>

    <div class="footer-actions">
      <span class="section-copy">创建完成后会直接进入任务详情页，下一步就能上传 PDF 简历。</span>
      <button class="primary-btn" type="button" :disabled="submitting" @click="submit">
        {{ submitting ? "创建中..." : "创建并进入任务" }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";

import { createTask } from "../../lib/gateway";

const router = useRouter();
const submitting = ref(false);
const errorMessage = ref("");

const form = reactive({
  title: "前端开发工程师第一轮筛选",
  role: "前端开发工程师",
  templateName: "前端通用模板",
  jdText: "需要 Vue、TypeScript、JavaScript 能力，负责在线考试与后台系统。"
});

async function submit() {
  if (!form.title.trim() || !form.role.trim() || !form.jdText.trim()) {
    errorMessage.value = "任务名称、岗位名称和 JD 不能为空。";
    return;
  }

  submitting.value = true;
  errorMessage.value = "";
  try {
    const task = await createTask({
      title: form.title.trim(),
      role: form.role.trim(),
      jdText: form.jdText.trim(),
      templateName: form.templateName.trim() || "通用模板"
    });
    await router.push({ name: "admin-task-detail", params: { taskId: task.id } });
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "创建任务失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.task-create-card {
  display: grid;
  gap: 20px;
  padding: 24px;
}

.page-head,
.footer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-title {
  margin: 16px 0 0;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
  color: var(--ink-soft);
}

.field--full {
  grid-column: 1 / -1;
}

.error-banner {
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(220, 38, 38, 0.1);
  color: var(--danger);
}

@media (max-width: 960px) {
  .page-head,
  .footer-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
