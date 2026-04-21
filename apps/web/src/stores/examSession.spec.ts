import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";

import { useExamSessionStore } from "./examSession";

describe("exam session store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("tracks draft answers by question id", () => {
    const store = useExamSessionStore();
    store.upsertDraftAnswer("q-1", { value: "Vue" });
    expect(store.answers["q-1"]).toEqual({ value: "Vue" });
  });
});
