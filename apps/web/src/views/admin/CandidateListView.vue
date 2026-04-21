<template>
  <section class="glass-card page-card">
    <div class="grid-two list-hero">
      <div>
        <div class="pill">Pipeline Snapshot</div>
        <h2 class="hero-title">把 PDF、画像、考卷草稿放到一个工作台里。</h2>
        <p class="hero-copy">
          面向 HR 的第一页不是表格堆砌，而是一张能看出优先级、解析质量和待处理动作的面板。
        </p>
      </div>
      <div class="grid-three">
        <article class="metric-tile" v-for="metric in metrics" :key="metric.label">
          <div class="metric-value">{{ metric.value }}</div>
          <div class="metric-label">{{ metric.label }}</div>
        </article>
      </div>
    </div>

    <div class="toolbar">
      <input class="soft-input" placeholder="搜索候选人 / 邮箱 / 岗位模板" />
      <select class="soft-select">
        <option>全部状态</option>
        <option>待解析</option>
        <option>待发卷</option>
        <option>已开考</option>
      </select>
    </div>

    <div class="candidate-grid">
      <article v-if="loading" class="candidate-card candidate-card--muted">
        <div class="candidate-name">正在同步候选人数据...</div>
        <p class="section-copy">Gateway 已接入，列表会优先读取后端返回，异常时自动回退到本地样例。</p>
      </article>
      <article class="candidate-card" v-for="candidate in candidates" :key="candidate.id">
        <div class="candidate-top">
          <div>
            <div class="candidate-name">{{ candidate.name }}</div>
            <div class="candidate-meta">{{ candidate.role }} · {{ candidate.city }}</div>
          </div>
          <span class="pill status-pill">{{ candidate.status }}</span>
        </div>
        <p class="section-copy">{{ candidate.summary }}</p>
        <div class="tag-row">
          <span class="tag-chip" v-for="tag in candidate.skills" :key="tag">{{ tag }}</span>
        </div>
        <div class="candidate-footer">
          <span>解析质量 {{ candidate.quality }}</span>
          <RouterLink class="secondary-btn inline-btn" :to="`/admin/candidates/${candidate.id}`">查看详情</RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { loadCandidates, type CandidateCard } from "../../lib/gateway";

const loading = ref(true);
const candidates = ref<CandidateCard[]>([]);

const metrics = computed(() => [
  { label: "今日待处理简历", value: String(candidates.value.length || 0) },
  {
    label: "待审核考卷草稿",
    value: String(candidates.value.filter((candidate) => candidate.status !== "已开考").length || 0)
  },
  {
    label: "自动解析置信高",
    value: candidates.value.length
      ? `${Math.round((candidates.value.filter((candidate) => candidate.quality === "高").length / candidates.value.length) * 100)}%`
      : "0%"
  }
]);

onMounted(async () => {
  candidates.value = await loadCandidates();
  loading.value = false;
});
</script>

<style scoped>
.page-card {
  padding: 28px;
}

.list-hero {
  align-items: center;
}

.toolbar {
  display: grid;
  grid-template-columns: 1fr 220px;
  gap: 16px;
  margin: 28px 0;
}

.candidate-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.candidate-card {
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.candidate-card--muted {
  opacity: 0.75;
}

.candidate-top,
.candidate-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.candidate-name {
  font-size: 1.1rem;
  font-weight: 700;
}

.candidate-meta,
.candidate-footer {
  color: var(--ink-soft);
  font-size: 0.92rem;
}

.tag-row {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin: 16px 0;
}

.tag-chip {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.06);
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.inline-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 960px) {
  .toolbar,
  .candidate-grid {
    grid-template-columns: 1fr;
  }
}
</style>
