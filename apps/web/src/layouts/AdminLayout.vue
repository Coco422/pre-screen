<template>
  <div class="admin-console">
    <AdminSidebarNav />

    <main class="admin-console__main">
      <AdminTopbar
        :title="currentTitle"
        :user-name="sessionStore.userName || 'HR_Admin'"
        @sign-out="signOut"
      />
      <AdminProcessingMonitorBar />
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { RouterView, useRoute, useRouter } from "vue-router";

import AdminProcessingMonitorBar from "../components/admin/AdminProcessingMonitorBar.vue";
import AdminSidebarNav from "../components/layout/AdminSidebarNav.vue";
import AdminTopbar from "../components/layout/AdminTopbar.vue";
import { useAdminSessionStore } from "../stores/adminSession";

const route = useRoute();
const router = useRouter();
const sessionStore = useAdminSessionStore();

onMounted(async () => {
  await sessionStore.restore();
});

const currentTitle = computed(() => String(route.meta.title ?? "工作台"));

function signOut() {
  sessionStore.signOut();
  void router.replace("/login");
}
</script>
