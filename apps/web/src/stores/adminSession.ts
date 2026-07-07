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
        this.session = persisted;
        try {
          this.session = await fetchAdminSession();
          persistSession(this.session);
        } catch {
          persistSession(this.session);
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
