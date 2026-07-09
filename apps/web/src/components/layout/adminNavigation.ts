export type AdminNavigationItem = {
  label: string;
  icon: string;
  to: { name: string };
  placeholder?: boolean;
};

export const adminNavigation: AdminNavigationItem[] = [
  { label: "工作台", icon: "HomeFilled", to: { name: "admin-dashboard" } },
  { label: "任务中心", icon: "Tickets", to: { name: "admin-tasks" } },
  { label: "候选人", icon: "UserFilled", to: { name: "admin-candidates" } },
  { label: "考卷管理", icon: "Document", to: { name: "admin-papers" }, placeholder: true },
  { label: "结果中心", icon: "DataAnalysis", to: { name: "admin-results" } },
  { label: "考试监控", icon: "WarningFilled", to: { name: "admin-monitor" } },
  { label: "AI 配置", icon: "Setting", to: { name: "admin-settings" } }
];
