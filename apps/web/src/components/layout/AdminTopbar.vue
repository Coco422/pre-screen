<template>
  <header class="admin-topbar">
    <div class="admin-topbar__heading">
      <h1 class="admin-topbar__title">{{ title }}</h1>
    </div>

    <div class="admin-topbar__actions">
      <el-tooltip content="消息中心（规划中）" placement="bottom">
        <el-badge is-dot class="admin-topbar__badge">
          <button class="admin-topbar__icon-btn" type="button" aria-label="通知" @click="openNotifications">
            <el-icon><Bell /></el-icon>
          </button>
        </el-badge>
      </el-tooltip>

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
            <el-dropdown-item command="profile">账号设置</el-dropdown-item>
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
import { useRouter } from "vue-router";

defineProps<{
  title: string;
  userName: string;
}>();

const emit = defineEmits<{
  (event: "sign-out"): void;
}>();

const router = useRouter();

function openNotifications() {
  void router.push({ name: "admin-settings", query: { tab: "notifications" } });
}

function handleCommand(command: string | number | object) {
  if (command === "sign-out") {
    emit("sign-out");
    return;
  }
  if (command === "profile" || command === "password") {
    void router.push({ name: "admin-settings", query: { tab: "account" } });
  }
}
</script>
