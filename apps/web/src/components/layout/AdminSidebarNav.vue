<template>
  <aside class="admin-sidebar">
    <div class="admin-sidebar__brand">
      <div class="admin-sidebar__logo">P</div>
      <div class="admin-sidebar__brand-copy">
        <strong>Pre-Screen</strong>
        <p>招聘预筛控制台</p>
      </div>
    </div>

    <nav class="admin-sidebar__nav" aria-label="主导航">
      <RouterLink
        v-for="item in adminNavigation"
        :key="item.label"
        class="admin-sidebar__item"
        :class="{ 'is-placeholder': item.placeholder }"
        :to="item.to"
      >
        <span class="admin-sidebar__item-icon" aria-hidden="true">
          <component :is="iconMap[item.icon]" />
        </span>
        <span class="admin-sidebar__item-label">{{ item.label }}</span>
      </RouterLink>
    </nav>
  </aside>
</template>

<script setup lang="ts">
import type { Component } from "vue";

import { DataAnalysis, Document, HomeFilled, Setting, Tickets, UserFilled, WarningFilled } from "@element-plus/icons-vue";
import { RouterLink } from "vue-router";

import { adminNavigation } from "./adminNavigation";

const iconMap: Record<string, Component> = {
  HomeFilled,
  Tickets,
  UserFilled,
  Document,
  DataAnalysis,
  WarningFilled,
  Setting
};
</script>
