import { defineStore } from "pinia";

export type DraftAnswer = Record<string, unknown>;

export const useExamSessionStore = defineStore("exam-session", {
  state: () => ({
    sessionToken: "",
    activeQuestionId: "q-base-1",
    answers: {} as Record<string, DraftAnswer>,
    lastHeartbeatAt: "",
    riskEvents: [] as Array<{ type: string; createdAt: string }>,
    startedAt: "",
    expiresAt: ""
  }),
  actions: {
    upsertDraftAnswer(questionId: string, value: DraftAnswer) {
      this.answers[questionId] = value;
    },
    markHeartbeat(timestamp: string) {
      this.lastHeartbeatAt = timestamp;
    },
    setSessionMeta(payload: { token: string; startedAt: string; expiresAt: string }) {
      this.sessionToken = payload.token;
      this.startedAt = payload.startedAt;
      this.expiresAt = payload.expiresAt;
    },
    setActiveQuestion(questionId: string) {
      this.activeQuestionId = questionId;
    },
    logRiskEvent(type: string) {
      this.riskEvents.push({ type, createdAt: new Date().toISOString() });
    },
    hydrateDrafts(answers: Record<string, DraftAnswer>) {
      this.answers = answers;
    }
  }
});
