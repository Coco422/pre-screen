<template>
  <section class="task-create-page">
    <header class="task-create-page__head">
      <div>
        <h2 class="task-create-page__title">新建筛选任务</h2>
        <p class="task-create-page__subtitle">填写任务基础信息和 JD，创建后进入任务详情上传简历。</p>
      </div>
      <RouterLink class="task-create-page__back" :to="{ name: 'admin-tasks' }">返回任务中心</RouterLink>
    </header>

    <section class="task-create-form">
      <div class="task-create-form__section">
        <h3>基础信息</h3>
        <div class="form-grid">
          <label class="field">
            <span>任务名称</span>
            <el-input v-model="form.title" placeholder="例如：前端开发工程师第一轮筛选" />
          </label>
          <label class="field">
            <span>岗位名称</span>
            <el-input v-model="form.role" placeholder="前端开发工程师" />
          </label>
          <label class="field field--full">
            <span>考卷模板</span>
            <el-select v-model="form.templateName" placeholder="请选择考卷模板">
              <el-option v-for="template in templateOptions" :key="template" :label="template" :value="template" />
            </el-select>
          </label>
        </div>
      </div>

      <div class="task-create-form__section">
        <h3>岗位 JD</h3>
        <label class="field">
          <textarea
            v-model="form.jdText"
            class="field-input field-textarea"
            rows="10"
            placeholder="写清楚技能要求、岗位职责和重点考察方向。"
          />
        </label>
      </div>

      <div v-if="errorMessage" class="error-banner">{{ errorMessage }}</div>

      <footer class="footer-actions">
        <span>创建完成后会直接进入任务详情页。</span>
        <button class="task-create-page__submit" type="button" :disabled="submitting" @click="submit">
          {{ submitting ? "创建中..." : "创建并进入任务" }}
        </button>
      </footer>
    </section>
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

const templateOptions = ["前端通用模板", "后端通用模板", "全栈工程师模板", "算法工程师模板", "通用模板"];

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
.task-create-page {
  display: grid;
  gap: 14px;
  min-height: 100%;
  padding: 14px 16px 16px;
  border-radius: 8px;
  background: #ffffff;
}

.task-create-page__head,
.footer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.task-create-page__head {
  padding-bottom: 12px;
  border-bottom: 1px solid #edf1f6;
}

.task-create-page__title {
  margin: 0;
  color: #17253d;
  font-size: 20px;
  font-weight: 800;
}

.task-create-page__subtitle {
  margin: 6px 0 0;
  color: #66758a;
  font-size: 13px;
}

.task-create-page__back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: none;
  height: 34px;
  padding: 0 12px;
  border: 1px solid #d7e2ef;
  border-radius: 4px;
  background: #ffffff;
  color: #40546f;
  font-size: 13px;
  font-weight: 700;
}

.task-create-form {
  display: grid;
  gap: 18px;
  /* max-width: 920px; */
}

.task-create-form__section {
  display: grid;
  gap: 12px;
}

.task-create-form__section h3 {
  margin: 0;
  color: #17253d;
  font-size: 16px;
  font-weight: 800;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px 16px;
}

.field {
  display: grid;
  gap: 8px;
  color: #40546f;
  font-size: 13px;
  font-weight: 700;
}

.field--full {
  grid-column: 1 / -1;
}

.field :deep(.el-input),
.field :deep(.el-select) {
  width: 100%;
}

.field :deep(.el-input__wrapper),
.field :deep(.el-select__wrapper) {
  min-height: 38px;
  border-radius: 4px;
  box-shadow: inset 0 0 0 1px #d7e2ef;
}

.field :deep(.el-input__wrapper.is-focus),
.field :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    inset 0 0 0 1px #7eaaef,
    0 0 0 3px rgba(47, 108, 246, 0.08);
}

.field-input {
  width: 100%;
  border: 1px solid #d7e2ef;
  border-radius: 4px;
  background: #ffffff;
  color: #17253d;
  outline: none;
  padding: 10px 12px;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.field-input:focus {
  border-color: #7eaaef;
  box-shadow: 0 0 0 3px rgba(47, 108, 246, 0.08);
}

.field-textarea {
  min-height: 220px;
  resize: vertical;
  line-height: 1.6;
}

.error-banner {
  padding: 10px 12px;
  border: 1px solid #f3c2c2;
  border-radius: 4px;
  background: #fff5f5;
  color: #c24141;
  font-size: 13px;
  font-weight: 700;
}

.footer-actions {
  padding-top: 14px;
  border-top: 1px solid #edf1f6;
}

.footer-actions span {
  color: #66758a;
  font-size: 13px;
}

.task-create-page__submit {
  height: 36px;
  padding: 0 16px;
  border: 1px solid #2f69d9;
  border-radius: 4px;
  background: #2f6cf6;
  color: #ffffff;
  cursor: pointer;
  font-weight: 700;
}

.task-create-page__submit:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

@media (max-width: 960px) {
  .task-create-page__head,
  .footer-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
