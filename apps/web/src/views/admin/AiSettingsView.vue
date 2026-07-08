<template>
  <section class="ai-settings-page">
    <header class="page-head">
      <h2 class="page-title">AI 模型配置</h2>
      <AdminToneBadge :label="connectionStatus" :tone="connectionTone" />
    </header>

    <form class="settings-form" @submit.prevent="saveSettings">
      <label class="field">
        <span>Base URL</span>
        <el-input v-model="form.baseUrl" placeholder="http://172.16.99.204:3398" />
      </label>

      <label class="field">
        <span>模型名称</span>
        <el-input v-model="form.model" placeholder="qwen3.6-27b" />
      </label>

      <label class="field">
        <span>API Key</span>
        <el-input
          v-model="form.apiKey"
          type="password"
          show-password
          :placeholder="maskedKey || 'sk-xxxxxxxx'"
        />
      </label>

      <div class="form-actions">
        <button class="primary-btn" type="submit" :disabled="saving">
          {{ saving ? "保存中..." : "保存" }}
        </button>
        <button class="secondary-btn" type="button" :disabled="testing" @click="testConnection">
          {{ testing ? "测试中..." : "测试连通性" }}
        </button>
      </div>

      <div v-if="message" class="status-message" :class="messageType">
        {{ message }}
      </div>
    </form>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";

import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "/api";

const form = reactive({
  baseUrl: "",
  model: "",
  apiKey: ""
});

const maskedKey = ref("");
const saving = ref(false);
const testing = ref(false);
const message = ref("");
const messageType = ref<"success" | "error">("success");
const testResult = ref<{ ok: boolean; latencyMs?: number } | null>(null);

const connectionStatus = computed(() => {
  if (testResult.value === null) return "未测试";
  return testResult.value.ok ? `可用 (${testResult.value.latencyMs}ms)` : "不可用";
});

const connectionTone = computed(() => {
  if (testResult.value === null) return "info" as const;
  return testResult.value.ok ? "success" as const : "danger" as const;
});

async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/admin/settings/ai`);
    if (!res.ok) return;
    const data = await res.json();
    form.baseUrl = data.base_url || "";
    form.model = data.model || "";
    maskedKey.value = data.api_key_masked || "";
  } catch {
    // ignore
  }
}

async function saveSettings() {
  saving.value = true;
  message.value = "";
  try {
    const body: Record<string, string> = {};
    if (form.baseUrl) body.base_url = form.baseUrl;
    if (form.model) body.model = form.model;
    if (form.apiKey) body.api_key = form.apiKey;

    const res = await fetch(`${API_BASE}/admin/settings/ai`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });

    if (!res.ok) throw new Error("保存失败");
    const data = await res.json();
    maskedKey.value = data.api_key_masked || maskedKey.value;
    form.apiKey = "";
    message.value = "已保存";
    messageType.value = "success";
  } catch (e) {
    message.value = e instanceof Error ? e.message : "保存失败";
    messageType.value = "error";
  } finally {
    saving.value = false;
  }
}

async function testConnection() {
  testing.value = true;
  message.value = "";
  testResult.value = null;
  try {
    const res = await fetch(`${API_BASE}/admin/settings/ai/test`, { method: "POST" });
    const data = await res.json();
    testResult.value = { ok: data.ok, latencyMs: data.latency_ms };
    message.value = data.ok ? `连通 (${data.latency_ms}ms)` : `失败: ${data.error}`;
    messageType.value = data.ok ? "success" : "error";
  } catch (e) {
    testResult.value = { ok: false };
    message.value = e instanceof Error ? e.message : "测试失败";
    messageType.value = "error";
  } finally {
    testing.value = false;
  }
}

onMounted(loadSettings);
</script>

<style scoped>
.ai-settings-page {
  display: grid;
  gap: 20px;
  padding: 16px 18px;
  border: 1px solid #d7e1ee;
  border-radius: 14px;
  background: #ffffff;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
}

.settings-form {
  display: grid;
  gap: 16px;
  max-width: 480px;
}

.field {
  display: grid;
  gap: 6px;
}

.field span {
  font-size: 13px;
  font-weight: 600;
  color: #3a5070;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.status-message {
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
}

.status-message.success {
  background: rgba(22, 163, 74, 0.08);
  color: #166534;
}

.status-message.error {
  background: rgba(220, 38, 38, 0.08);
  color: #991b1b;
}
</style>
