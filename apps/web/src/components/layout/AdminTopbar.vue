<template>
  <header class="admin-topbar">
    <div class="admin-topbar__heading">
      <h1 class="admin-topbar__title">{{ title }}</h1>
    </div>

    <div class="admin-topbar__actions">
      <el-badge :value="1" class="admin-topbar__badge">
        <button class="admin-topbar__icon-btn" type="button" aria-label="通知">
          <el-icon><Bell /></el-icon>
        </button>
      </el-badge>

      <el-avatar class="admin-topbar__avatar" :size="32">
        <el-icon><UserFilled /></el-icon>
      </el-avatar>

      <el-dropdown trigger="click" @command="handleCommand">
        <button class="admin-topbar__user-menu" type="button">
          <span>{{ userName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">修改用户信息</el-dropdown-item>
            <el-dropdown-item command="password">修改密码</el-dropdown-item>
            <el-dropdown-item divided command="sign-out">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ArrowDown, Bell, UserFilled } from "@element-plus/icons-vue";

defineProps<{
  title: string;
  userName: string;
}>();

const emit = defineEmits<{
  (event: "sign-out"): void;
}>();

function handleCommand(command: string | number | object) {
  if (command === "sign-out") {
    emit("sign-out");
  }
}
</script>
