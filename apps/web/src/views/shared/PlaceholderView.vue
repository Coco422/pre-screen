<template>
  <section class="placeholder-page">
    <el-empty :description="description">
      <template #image>
        <div class="placeholder-mark">{{ iconLabel }}</div>
      </template>
      <el-button v-if="actionLabel" type="primary" @click="emit('action')">{{ actionLabel }}</el-button>
    </el-empty>
  </section>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  action: [];
}>();

defineProps<{
  description: string;
  iconLabel?: string;
  actionLabel?: string;
}>();
</script>
