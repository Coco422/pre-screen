<template>
  <section v-if="profile" class="detail-grid">
    <article class="glass-card detail-card">
      <div class="pill">Candidate Profile</div>
      <div class="profile-heading">
        <img v-if="profile.avatarUrl" class="avatar" :src="profile.avatarUrl" :alt="`${profile.name} 头像`" />
        <div v-else class="avatar avatar--empty">无头像</div>
        <div>
          <h2 class="section-title detail-title">{{ profile.name }}</h2>
          <p class="section-copy">
            {{ profile.role }} · {{ profile.city }}
          </p>
          <p class="section-copy contact-line">
            {{ profile.phone || "手机号未识别" }} · {{ profile.email || "邮箱未识别" }}
          </p>
        </div>
      </div>
      <div class="tag-row">
        <span class="tag-chip" v-for="skill in profile.skills" :key="skill">{{ skill }}</span>
      </div>
      <div class="detail-section">
        <h3>项目摘要</h3>
        <p>{{ profile.projectSummary }}</p>
      </div>
      <div class="detail-section">
        <h3>异常与补读</h3>
        <ul>
          <li v-for="note in profile.reviewNotes" :key="note">{{ note }}</li>
        </ul>
      </div>
    </article>

    <article class="glass-card detail-card">
      <div class="pill">Resume Intelligence</div>
      <div class="metric-list">
        <div class="metric-tile">
          <div class="metric-value">{{ profile.parseMetrics.firstPageCharacters }}</div>
          <div class="metric-label">首页文本字符</div>
        </div>
        <div class="metric-tile">
          <div class="metric-value">{{ profile.parseMetrics.multimodalPages }}</div>
          <div class="metric-label">多模态兜底页</div>
        </div>
        <div class="metric-tile">
          <div class="metric-value">{{ profile.parseMetrics.confidence }}</div>
          <div class="metric-label">解析置信度</div>
        </div>
      </div>
      <div class="detail-section">
        <h3>下一步动作</h3>
        <div class="button-row">
          <RouterLink
            v-for="action in profile.nextActions"
            :key="action.label"
            :class="action.label.includes('生成') ? 'primary-btn' : 'secondary-btn'"
            :to="action.target"
          >
            {{ action.label }}
          </RouterLink>
        </div>
      </div>
      <div class="detail-section">
        <h3>Markdown 预览</h3>
        <pre class="markdown-preview">{{ profile.markdownPreview }}</pre>
      </div>
    </article>
  </section>

  <section v-else class="glass-card loading-card">
    <div class="pill">Candidate Profile</div>
    <h2 class="section-title">正在加载候选人画像...</h2>
    <p class="section-copy">如果 Gateway 暂不可用，页面会自动回退到本地样例数据。</p>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";

import { loadCandidateDetail, type CandidateDetail } from "../../lib/gateway";

const route = useRoute();
const profile = ref<CandidateDetail | null>(null);

watch(
  () => route.params.candidateId,
  async (candidateId) => {
    if (typeof candidateId !== "string") {
      return;
    }
    profile.value = await loadCandidateDetail(candidateId);
  },
  { immediate: true }
);
</script>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 24px;
}

.detail-card {
  padding: 24px;
}

.detail-title {
  margin: 0;
  font-size: 2rem;
}

.profile-heading {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-top: 18px;
}

.avatar {
  width: 86px;
  height: 112px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid rgba(20, 33, 61, 0.12);
  background: rgba(255, 255, 255, 0.72);
  flex: 0 0 auto;
}

.avatar--empty {
  display: grid;
  place-items: center;
  color: var(--ink-soft);
  font-size: 0.84rem;
}

.contact-line {
  margin-top: 6px;
}

.detail-section {
  margin-top: 24px;
}

.detail-section h3 {
  margin: 0 0 10px;
}

.detail-section p,
.detail-section li {
  color: var(--ink-soft);
  line-height: 1.7;
}

.markdown-preview {
  max-height: 360px;
  overflow: auto;
  padding: 14px;
  border-radius: 8px;
  background: rgba(20, 33, 61, 0.06);
  color: var(--ink);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.86rem;
  line-height: 1.6;
  white-space: pre-wrap;
}

.metric-list {
  display: grid;
  gap: 16px;
  margin-top: 20px;
}

.button-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

@media (max-width: 960px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
