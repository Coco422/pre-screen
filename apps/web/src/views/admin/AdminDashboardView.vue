<template>
  <section class="dashboard-page">
    <div v-if="loading" class="dashboard-state-card">正在同步工作台数据...</div>

    <template v-else>
      <div v-if="loadError" class="dashboard-error-banner" role="alert">
        <strong>工作台同步失败</strong>
        <span>{{ loadError }}</span>
      </div>

      <div class="dashboard-metrics">
        <article v-for="metric in metrics" :key="metric.label" class="dashboard-metric">
          <p>{{ metric.label }}</p>
          <strong>{{ metric.value }}</strong>
        </article>
      </div>

      <div class="dashboard-columns">
        <section class="page-panel dashboard-region">
          <div class="dashboard-region__head">
            <div>
              <h2>待处理候选人</h2>
            </div>
            <RouterLink :to="{ name: 'admin-candidates' }">查看全部</RouterLink>
          </div>

          <el-table :data="priorityCandidates" stripe>
            <el-table-column prop="name" label="姓名" />
            <el-table-column prop="role" label="岗位" />
            <el-table-column prop="status" label="状态" />
          </el-table>
        </section>

        <section class="page-panel dashboard-region">
          <div class="dashboard-region__head">
            <div>
              <h2>最近任务</h2>
            </div>
            <RouterLink :to="{ name: 'admin-tasks' }">进入</RouterLink>
          </div>

          <el-table :data="tasks" stripe>
            <el-table-column prop="title" label="任务名称" />
            <el-table-column prop="role" label="岗位" />
            <el-table-column prop="status" label="状态" />
          </el-table>
        </section>

        <section class="page-panel dashboard-region">
          <div class="dashboard-region__head">
            <div>
              <h2>最新结果</h2>
            </div>
            <RouterLink :to="{ name: 'admin-results' }">结果中心</RouterLink>
          </div>

          <el-table :data="results" stripe>
            <el-table-column prop="candidateName" label="姓名" />
            <el-table-column prop="role" label="岗位" />
            <el-table-column prop="totalScore" label="总分" />
          </el-table>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { RouterLink } from "vue-router";

import { loadCandidates, loadResults, loadTasks, type CandidateCard, type ResultSummary, type ScreeningTaskSummary } from "../../lib/gateway";

const actionableStatusSet = new Set(["待审核", "待发卷", "已发卷"]);
const loading = ref(true);
const loadError = ref("");
const tasks = ref<ScreeningTaskSummary[]>([]);
const candidates = ref<CandidateCard[]>([]);
const results = ref<ResultSummary[]>([]);

const actionableCandidates = computed(() => candidates.value.filter((candidate) => actionableStatusSet.has(candidate.status)));
const priorityCandidates = computed(() => actionableCandidates.value.slice(0, 5));

const metrics = computed(() => [
  { label: "待处理候选人", value: String(actionableCandidates.value.length) },
  { label: "待发卷人数", value: String(candidates.value.filter((item) => item.status === "待发卷").length) },
  { label: "进行中考试", value: String(candidates.value.filter((item) => item.status === "已开考").length) },
  { label: "已完成作答", value: String(results.value.length) },
  { label: "异常事件", value: String(candidates.value.filter((item) => item.processing?.status === "error").length) }
]);

onMounted(async () => {
  loading.value = true;
  loadError.value = "";

  const [taskItems, candidateItems, resultItems] = await Promise.allSettled([loadTasks(), loadCandidates(), loadResults()]);
  const failedSections: string[] = [];

  if (taskItems.status === "fulfilled") {
    tasks.value = taskItems.value;
  } else {
    failedSections.push("任务");
  }

  if (candidateItems.status === "fulfilled") {
    candidates.value = candidateItems.value;
  } else {
    failedSections.push("候选人");
  }

  if (resultItems.status === "fulfilled") {
    results.value = resultItems.value;
  } else {
    failedSections.push("结果");
  }

  loadError.value = failedSections.length ? `${failedSections.join("、")}数据加载失败，已显示可用内容。` : "";
  loading.value = false;
});
</script>
