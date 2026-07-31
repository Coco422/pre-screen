import { defineStore } from "pinia";

import { fetchAdminSession, loginAdmin, type AdminSession } from "../lib/gateway";

const STORAGE_KEY = "pre-screen:admin-session";

function readPersistedSession(): AdminSession | null {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as AdminSession;
  } catch {
    return null;
  }
}

function persistSession(session: AdminSession | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (session) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    return;
  }

  window.localStorage.removeItem(STORAGE_KEY);
}

export function hasAdminSession() {
  return Boolean(readPersistedSession()?.sessionToken);
}

export const useAdminSessionStore = defineStore("admin-session", {
  state: () => ({
    session: readPersistedSession() as AdminSession | null,
    ready: false
  }),
  getters: {
    isLoggedIn: (state) => Boolean(state.session?.sessionToken),
    userName: (state) => state.session?.userName ?? "",
    role: (state) => state.session?.role ?? ""
  },
  actions: {
    async restore() {
      if (this.ready) {
        return;
      }

      const persisted = readPersistedSession();
      if (persisted) {
        try {
          this.session = await fetchAdminSession();
          persistSession(this.session);
        } catch {
          // Fail closed：以服务端校验为权威，任何校验失败都丢弃本地会话，
          // 避免带着过期或伪造凭证进入管理端。
          this.session = null;
          persistSession(null);
        }
      }

      this.ready = true;
    },
    async signIn(username: string, password: string) {
      this.session = await loginAdmin(username, password);
      this.ready = true;
      persistSession(this.session);
      return this.session;
    },
    signOut() {
      this.session = null;
      this.ready = true;
      persistSession(null);
    }
  }
});
