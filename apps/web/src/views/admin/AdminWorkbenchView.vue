<template>
  <section class="glass-card page-card">
    <div class="page-head">
      <div>
        <div class="pill">Workbench</div>
        <h2 class="section-title page-title">今日初筛工作台</h2>
        <p class="section-copy">{{ workbenchNarrative }}</p>
      </div>
      <div class="head-actions">
        <RouterLink class="secondary-btn" :to="{ name: 'admin-results' }">查看结果</RouterLink>
        <RouterLink class="primary-btn" :to="{ name: 'admin-task-create' }">新建筛选任务</RouterLink>
      </div>
    </div>

    <section class="hero-grid">
      <article class="hero-card hero-card--accent">
        <div class="hero-card__eyebrow">建议下一步</div>
        <h3>{{ nextAction.title }}</h3>
        <p>{{ nextAction.copy }}</p>
        <RouterLink class="primary-btn hero-card__cta" :to="nextAction.to">{{ nextAction.cta }}</RouterLink>
      </article>

      <article class="hero-card">
        <div class="hero-card__eyebrow">今日待办</div>
        <div class="todo-list">
          <RouterLink v-for="item in todoItems" :key="item.label" class="todo-item" :to="item.to">
            <div>
              <strong>{{ item.label }}</strong>
              <p>{{ item.copy }}</p>
            </div>
            <span class="todo-item__count">{{ item.count }}</span>
          </RouterLink>
        </div>
      </article>
    </section>

    <div class="metric-grid">
      <article class="metric-tile" v-for="metric in metrics" :key="metric.label">
        <div class="metric-value">{{ metric.value }}</div>
        <div class="metric-label">{{ metric.label }}</div>
      </article>
    </div>

    <div v-if="loadError" class="error-banner">
      <strong>工作台同步失败</strong>
      <span>{{ loadError }}</span>
    </div>

    <div class="workbench-layout">
      <section class="panel-card">
        <div class="panel-head">
          <div>
            <h3>进行中的筛选任务</h3>
            <p class="panel-copy">从这里继续查看岗位筛选状态、候选人数量和任务详情。</p>
          </div>
          <RouterLink class="text-link" :to="{ name: 'admin-task-create' }">新建任务</RouterLink>
        </div>

        <div v-if="loading" class="empty-state">正在同步任务...</div>

        <div v-else class="task-list">
          <article class="task-item" v-for="task in tasks" :key="task.id">
            <div class="task-main">
              <div class="task-title-row">
                <strong>{{ task.title }}</strong>
                <span class="pill task-status">{{ task.status }}</span>
              </div>
              <div class="task-meta">
                {{ task.role }} · 简历 {{ task.uploadCount }} · 候选人 {{ task.candidateCount }} · 创建于 {{ formatDate(task.createdAt) }}
              </div>
            </div>
            <div class="task-actions">
              <RouterLink class="secondary-btn inline-btn" :to="buildTaskDetailPath(task.id)">查看任务</RouterLink>
            </div>
          </article>

          <div v-if="!tasks.length" class="empty-state">还没有筛选任务。先创建一个任务，后面上传 PDF、发卷和查看结果都会更顺手。</div>
        </div>
      </section>

      <section class="panel-card">
        <div class="panel-head">
          <div>
            <h3>待处理候选人</h3>
            <p class="panel-copy">优先展示最需要你接手的候选人，减少来回切列表。</p>
          </div>
          <RouterLink class="text-link" :to="{ name: 'admin-candidates' }">查看全部</RouterLink>
        </div>

        <div v-if="loading" class="empty-state">正在同步候选人...</div>

        <div v-else class="shortcut-list">
          <RouterLink
            v-for="candidate in priorityCandidates"
            :key="candidate.id"
            class="shortcut-item"
            :to="buildCandidateDetailPath(candidate.id)"
          >
            <div>
              <span>{{ candidate.name }} · {{ candidate.status }}</span>
              <p>{{ candidate.summary }}</p>
            </div>
            <strong>{{ candidate.role }}</strong>
          </RouterLink>

          <div v-if="!priorityCandidates.length" class="empty-state">当前没有待处理候选人。新发卷或新简历进来后，这里会优先提醒。</div>
        </div>
      </section>
    </div>

    <section class="panel-card">
      <div class="panel-head">
        <div>
          <h3>最近完成的作答</h3>
          <p class="panel-copy">已交卷结果会按最近提交排序，方便你第一时间回看高优先级候选人。</p>
        </div>
        <RouterLink class="text-link" :to="{ name: 'admin-results' }">结果列表</RouterLink>
      </div>

      <div v-if="loading" class="empty-state">正在同步结果...</div>

      <div v-else class="result-list">
        <RouterLink
          v-for="result in recentResults"
          :key="result.resultId"
          class="result-item"
          :to="buildResultDetailPath(result.resultId)"
        >
          <div>
            <span>{{ result.candidateName }} · {{ result.role }}</span>
            <p>{{ result.status }} · 提交于 {{ formatDate(result.submittedAt) }}</p>
          </div>
          <strong>{{ result.totalScore }} 分</strong>
        </RouterLink>

        <div v-if="!recentResults.length" class="empty-state">还没有已交卷结果。等候选人完成作答后，这里会持续更新。</div>
      </div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import {
  buildCandidateDetailPath,
  buildResultDetailPath,
  buildTaskDetailPath
} from "../../components/admin/adminRouting";
import { loadCandidates, loadResults, loadTasks, type CandidateCard, type ResultSummary, type ScreeningTaskSummary } from "../../lib/gateway";

const loading = ref(true);
const loadError = ref("");
const tasks = ref<ScreeningTaskSummary[]>([]);
const candidates = ref<CandidateCard[]>([]);
const results = ref<ResultSummary[]>([]);

const pendingReviewCandidates = computed(() => candidates.value.filter((candidate) => candidate.status === "待审核"));
const readyInviteCandidates = computed(() => candidates.value.filter((candidate) => candidate.status === "待发卷"));
const invitedCandidates = computed(() => candidates.value.filter((candidate) => candidate.status === "已发卷"));
const priorityCandidates = computed(() =>
  candidates.value.filter((candidate) => ["待审核", "待发卷", "已发卷"].includes(candidate.status)).slice(0, 4)
);
const recentResults = computed(() => [...results.value].sort((a, b) => b.submittedAt.localeCompare(a.submittedAt)).slice(0, 4));
const metrics = computed(() => [
  { label: "任务数", value: String(tasks.value.length) },
  { label: "候选人", value: String(candidates.value.length) },
  { label: "待审核候选人", value: String(pendingReviewCandidates.value.length) },
  { label: "已交卷", value: String(results.value.length) }
]);
const workbenchNarrative = computed(() => {
  if (loading.value) {
    return "系统正在整理今日任务、候选人和结果摘要。";
  }
  if (!tasks.value.length) {
    return "今天还没有筛选任务，先建任务，后续上传简历和发卷会更顺畅。";
  }
  if (readyInviteCandidates.value.length) {
    return `有 ${readyInviteCandidates.value.length} 位候选人已经准备好发卷，适合优先推进。`;
  }
  if (pendingReviewCandidates.value.length) {
    return `有 ${pendingReviewCandidates.value.length} 位候选人待审核，建议先完成简历判断，再决定是否发卷。`;
  }
  if (invitedCandidates.value.length) {
    return `有 ${invitedCandidates.value.length} 位候选人已发卷，建议关注作答完成情况和结果回收。`;
  }
  if (results.value.length) {
    return "候选人的作答结果已经回流，可以直接进入结果页开始复盘。";
  }
  return "当前工作台已经同步完成，你可以继续补充任务、上传简历或回看历史结果。";
});
const nextAction = computed(() => {
  if (!tasks.value.length) {
    return {
      title: "先新建一个筛选任务",
      copy: "任务是上传简历、组织候选人和发卷流程的起点，建好后后续动作会清晰很多。",
      cta: "去新建任务",
      to: { name: "admin-task-create" }
    };
  }

  if (readyInviteCandidates.value.length) {
    return {
      title: "优先处理待发卷候选人",
      copy: `目前有 ${readyInviteCandidates.value.length} 位候选人已经到了发卷节点，尽快推进可以缩短整体筛选周期。`,
      cta: "去看候选人",
      to: { name: "admin-candidates" }
    };
  }

  if (pendingReviewCandidates.value.length) {
    return {
      title: "先完成待审核候选人的简历判断",
      copy: `还有 ${pendingReviewCandidates.value.length} 位候选人等待你做第一轮判断，处理完之后就能决定是否发卷。`,
      cta: "去审核候选人",
      to: buildCandidateDetailPath(pendingReviewCandidates.value[0].id)
    };
  }

  if (invitedCandidates.value.length) {
    return {
      title: "跟进已发卷候选人的作答进度",
      copy: `目前有 ${invitedCandidates.value.length} 位候选人已经收到试卷，适合继续关注提交情况。`,
      cta: "查看候选人进度",
      to: buildCandidateDetailPath(invitedCandidates.value[0].id)
    };
  }

  if (recentResults.value.length) {
    return {
      title: "进入结果页回看最新作答",
      copy: "今天已经有候选人完成交卷，直接看结果页能最快形成判断。",
      cta: "查看结果",
      to: buildResultDetailPath(recentResults.value[0].resultId)
    };
  }

  return {
    title: "继续扩充当前筛选任务",
    copy: "任务已经创建完毕，下一步适合继续上传简历或补充候选人。",
    cta: "查看任务",
    to: buildTaskDetailPath(tasks.value[0].id)
  };
});
const todoItems = computed(() => [
  {
    label: "待审核候选人",
    count: String(pendingReviewCandidates.value.length),
    copy: "先做第一轮简历筛查，决定是否值得继续推进。",
    to: { name: "admin-candidates" }
  },
  {
    label: "待发卷候选人",
    count: String(readyInviteCandidates.value.length),
    copy: "这批候选人已经接近发卷节点，适合优先推进。",
    to: { name: "admin-candidates" }
  },
  {
    label: "已交卷结果",
    count: String(results.value.length),
    copy: "结果已经回流时，尽快复盘可以更快形成候选人判断。",
    to: { name: "admin-results" }
  }
]);

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false
  }).format(new Date(value));
}

onMounted(async () => {
  loading.value = true;
  loadError.value = "";

  try {
    const [taskItems, candidateItems, resultItems] = await Promise.all([loadTasks(), loadCandidates(), loadResults()]);
    tasks.value = taskItems;
    candidates.value = candidateItems;
    results.value = resultItems;
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : "工作台加载失败，请稍后重试。";
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.page-card {
  display: grid;
  gap: 24px;
  padding: 24px;
}

.page-head,
.panel-head,
.task-title-row,
.task-actions,
.result-item,
.shortcut-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.page-title {
  margin: 16px 0 0;
}

.head-actions,
.task-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.hero-grid,
.workbench-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(320px, 0.9fr);
  gap: 20px;
}

.hero-card,
.panel-card {
  display: grid;
  gap: 18px;
  padding: 20px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(20, 33, 61, 0.07);
}

.hero-card--accent {
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(255, 255, 255, 0.9));
}

.hero-card__eyebrow {
  color: var(--accent-strong);
  font-size: 0.85rem;
  font-weight: 700;
}

.hero-card h3,
.panel-head h3 {
  margin: 0;
}

.hero-card p,
.panel-copy,
.task-meta,
.empty-state,
.shortcut-item p,
.result-item p {
  margin: 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

.hero-card__cta {
  justify-self: start;
}

.todo-list,
.task-list,
.shortcut-list,
.result-list {
  display: grid;
  gap: 14px;
}

.todo-item,
.task-item,
.shortcut-item,
.result-item {
  padding: 16px;
  border-radius: 18px;
  background: rgba(20, 33, 61, 0.04);
}

.todo-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.todo-item p {
  margin: 6px 0 0;
  color: var(--ink-soft);
  line-height: 1.6;
}

.todo-item__count {
  min-width: 48px;
  height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.92);
  font-weight: 700;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.text-link {
  color: var(--accent-strong);
  font-weight: 600;
}

.task-main,
.shortcut-item > div,
.result-item > div {
  display: grid;
  gap: 8px;
}

.error-banner {
  display: grid;
  gap: 4px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(220, 38, 38, 0.1);
  color: var(--danger);
}

@media (max-width: 960px) {
  .page-head,
  .panel-head,
  .task-title-row,
  .task-actions,
  .result-item,
  .shortcut-item {
    align-items: flex-start;
    flex-direction: column;
  }

  .metric-grid,
  .hero-grid,
  .workbench-layout {
    grid-template-columns: 1fr;
  }
}
</style>
