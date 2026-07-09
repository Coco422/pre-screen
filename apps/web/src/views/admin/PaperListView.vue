<template>
  <section class="paper-list-page">
    <header class="page-head">
      <div>
        <h2 class="page-title">考卷管理</h2>
        <p class="page-meta">草稿与已发布考卷 · 共 {{ papers.length }} 份</p>
      </div>
      <div class="head-actions">
        <el-select v-model="statusFilter" clearable placeholder="全部状态" style="width: 140px">
          <el-option label="草稿" value="draft" />
          <el-option label="已发布" value="published" />
        </el-select>
        <button class="secondary-btn" type="button" :disabled="loading" @click="refresh">
          {{ loading ? "刷新中..." : "刷新" }}
        </button>
      </div>
    </header>

    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <div v-if="loading && !papers.length" class="glass-card empty-card">加载中</div>
    <div v-else-if="!filteredPapers.length" class="glass-card empty-card">
      暂无考卷。请在任务详情对候选人点击「生成考卷」。
    </div>

    <div v-else class="paper-grid">
      <article v-for="paper in filteredPapers" :key="paper.paperId" class="glass-card paper-card">
        <div class="paper-top">
          <div>
            <strong>{{ paper.title }}</strong>
            <div class="muted">{{ paper.candidateName }} · {{ paper.questionCount }} 题</div>
          </div>
          <AdminToneBadge
            :label="paper.status === 'published' ? '已发布' : '草稿'"
            :tone="paper.status === 'published' ? 'success' : 'warning'"
          />
        </div>
        <div class="muted">更新 {{ formatTime(paper.updatedAt) }} · 时长 {{ paper.durationMinutes }} 分钟</div>
        <div class="paper-actions">
          <RouterLink
            class="primary-action inline-btn"
            :to="{
              name: 'admin-paper-editor',
              params: { paperId: paper.paperId },
              query: { candidateId: paper.candidateId, candidateName: paper.candidateName }
            }"
          >
            {{ paper.status === "published" ? "查看 / 再发布" : "编辑并发布" }}
          </RouterLink>
          <RouterLink
            class="outline-btn inline-btn"
            :to="{ name: 'admin-candidate-detail', params: { candidateId: paper.candidateId } }"
          >
            候选人
          </RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import AdminToneBadge from "../../components/admin/AdminToneBadge.vue";
import { loadPapers, type PaperListItem } from "../../lib/gateway";

const papers = ref<PaperListItem[]>([]);
const loading = ref(false);
const errorMessage = ref("");
const statusFilter = ref("");

const filteredPapers = computed(() => {
  if (!statusFilter.value) {
    return papers.value;
  }
  return papers.value.filter((item) => item.status === statusFilter.value);
});

function formatTime(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleString("zh-CN", { hour12: false });
}

async function refresh() {
  loading.value = true;
  errorMessage.value = "";
  try {
    papers.value = await loadPapers();
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void refresh();
});
</script>

<style scoped>
.paper-list-page {
  display: grid;
  gap: 16px;
}

.page-head,
.paper-top,
.paper-actions,
.head-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.page-title {
  margin: 0;
}

.page-meta,
.muted,
.error-message {
  color: var(--ink-soft);
}

.error-message {
  color: #8f1f2f;
}

.paper-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.paper-card,
.empty-card {
  padding: 18px;
  display: grid;
  gap: 12px;
}

.inline-btn {
  text-decoration: none;
}

@media (max-width: 900px) {
  .paper-grid {
    grid-template-columns: 1fr;
  }
}
</style>
