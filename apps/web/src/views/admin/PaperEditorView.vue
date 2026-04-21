<template>
  <section v-if="paper" class="glass-card paper-card">
    <div class="paper-head">
      <div>
        <div class="pill">Paper Draft</div>
        <h2 class="section-title paper-title">{{ paper.title }}</h2>
        <p class="section-copy">模板为主 + JD 微调。HR 可以在发卷前调整题目顺序、分值和文案。</p>
      </div>
      <div class="button-row">
        <button class="secondary-btn">保存草稿</button>
        <button class="primary-btn">生成链接与验证码</button>
      </div>
    </div>

    <div class="paper-layout">
      <aside class="outline-panel">
        <div class="outline-title">题目结构</div>
        <div class="outline-item" v-for="item in outline" :key="item.label">
          <span>{{ item.label }}</span>
          <strong>{{ item.count }}</strong>
        </div>
      </aside>

      <div class="question-stack">
        <article class="question-card" v-for="question in paper.questions" :key="question.title">
          <div class="question-top">
            <div>
              <div class="question-type">{{ question.type }}</div>
              <h3>{{ question.title }}</h3>
            </div>
            <span class="pill">{{ question.score }} 分</span>
          </div>
          <p class="section-copy">{{ question.description }}</p>
        </article>
      </div>
    </div>
  </section>

  <section v-else class="glass-card paper-card">
    <div class="pill">Paper Draft</div>
    <h2 class="section-title paper-title">正在同步考卷草稿...</h2>
    <p class="section-copy">编辑器优先读取 Gateway 返回的草稿详情，异常时会回退到本地样例。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { loadPaperDraft, type PaperDraft } from "../../lib/gateway";

const route = useRoute();
const paper = ref<PaperDraft | null>(null);

const outline = computed(() => {
  if (!paper.value) {
    return [];
  }

  return [
    { label: "基础信息", count: paper.value.mix.base_info ?? 0 },
    { label: "客观题", count: paper.value.mix.objective ?? 0 },
    { label: "主观题", count: paper.value.mix.subjective ?? 0 },
    { label: "代码题", count: paper.value.mix.coding ?? 0 }
  ];
});

watch(
  () => route.params.paperId,
  async (paperId) => {
    if (typeof paperId !== "string") {
      return;
    }
    paper.value = await loadPaperDraft(paperId);
  },
  { immediate: true }
);
</script>

<style scoped>
.paper-card {
  padding: 24px;
}

.paper-head,
.question-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.paper-title {
  margin-top: 16px;
  font-size: 2rem;
}

.paper-layout {
  display: grid;
  grid-template-columns: 260px minmax(0, 1fr);
  gap: 24px;
  margin-top: 24px;
}

.outline-panel {
  padding: 18px;
  border-radius: 22px;
  background: rgba(20, 33, 61, 0.04);
}

.outline-title {
  font-weight: 700;
}

.outline-item {
  display: flex;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px solid rgba(20, 33, 61, 0.06);
}

.question-stack {
  display: grid;
  gap: 16px;
}

.question-card {
  padding: 18px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.question-type {
  color: var(--accent-strong);
  font-size: 0.88rem;
  font-weight: 700;
}

.question-card h3 {
  margin: 8px 0 0;
}

@media (max-width: 960px) {
  .paper-head,
  .paper-layout {
    grid-template-columns: 1fr;
    flex-direction: column;
  }
}
</style>
