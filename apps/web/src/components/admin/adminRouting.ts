type AdminAction = {
  label?: string;
  target?: string;
};

const DEFAULT_PAPER_ID = "new";

export function buildCandidateDetailPath(candidateId: string): string {
  return `/admin/candidates/${candidateId}`;
}

export function buildCandidateEditPath(candidateId: string): string {
  return `/admin/candidates/${candidateId}/edit`;
}

export function buildTaskDetailPath(taskId: string): string {
  return `/admin/tasks/${taskId}`;
}

export function buildTaskCreatePath(): string {
  return "/admin/tasks/new";
}

export function buildPaperEditorPath(paperId?: string | null): string {
  return `/admin/papers/${paperId || DEFAULT_PAPER_ID}`;
}

export function buildResultsPath(): string {
  return "/admin/results";
}

export function buildResultDetailPath(resultId: string): string {
  return `/admin/results/${resultId}`;
}

export function buildPaperRouteTarget(candidateId: string, nextActions: AdminAction[] = []) {
  const actionWithPaper = nextActions.find(
    (action) => typeof action.target === "string" && action.target.includes("/admin/papers/")
  );
  const paperId = actionWithPaper?.target?.match(/\/admin\/papers\/([^/?#]+)/)?.[1] ?? DEFAULT_PAPER_ID;

  return {
    path: `/admin/papers/${paperId}`,
    query: {
      candidateId
    }
  };
}
