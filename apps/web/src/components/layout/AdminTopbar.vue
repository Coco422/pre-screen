<template>
  <header class="admin-topbar">
    <div>
      <h1 class="admin-topbar__title">{{ title }}</h1>
    </div>

    <div class="admin-topbar__actions">
      <el-badge :value="1" class="admin-topbar__badge">
        <el-button aria-label="通知">
          <el-icon><Bell /></el-icon>
        </el-button>
      </el-badge>
      <div class="admin-topbar__user">{{ userName }}</div>
      <button class="secondary-btn admin-topbar__signout" type="button" @click='emit("sign-out")'>
        退出登录
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Bell } from "@element-plus/icons-vue";

defineProps<{
  title: string;
  userName: string;
}>();

const emit = defineEmits<{
  (event: "sign-out"): void;
}>();
</script>
