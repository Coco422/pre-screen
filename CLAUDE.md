# Repo Agent Context

This is the root routing contract for Claude Code and Codex. Keep it short:
load this first, then follow the repo-owned artifacts it names.

## Root Workflow Contract

- Keep sibling `CLAUDE.md` and `AGENTS.md` files aligned. Claude Code consumes `CLAUDE.md`; Codex consumes `AGENTS.md`.
- Prefer repo-local workflow artifacts over tool-specific chat memory.
- Treat `docs/spec.md` as stable product truth, `tasks/current.md` as a derived status snapshot, and `tasks/todos.md` as the deferred-goal ledger; current execution stays in the active plan's `## Task Breakdown`.
- Treat `docs/researches/`, `tasks/lessons.md`, `tasks/notes/`, `.ai/harness/policy.json`, and `.ai/harness/handoff/current.md` as durable workflow context.
- Use `.ai/context/context-map.json` and `.ai/context/capabilities.json` to discover functional-block contracts before adding local agent files.
- Do not infer local `CLAUDE.md` or `AGENTS.md` files from broad physical layouts such as `apps/*`, `packages/*`, or `services/*`.
- Put capability-specific ownership, entrypoints, and verification commands in explicitly selected functional-block contracts.
- Keep root context concise; route deep implementation detail into plans, task notes, research, workstreams, or architecture docs.
- Treat `_ref/` as ignored external reference material and `_ops/` as ignored local operations state.

## Agent Context Scaffolding

- Before creating or changing agent context files, inspect existing high-context files, repo manifests, CI workflows, Makefiles, generated outputs, generators, and high-risk directories.
- Treat scanners as leads, not authority. Verify commands, ownership, and generated-file boundaries against actual repo files before writing instructions.
- Choose the smallest instruction stack that changes behavior: root context for repo-wide routing, scoped context only where local rules differ, and no nested file for ordinary implementation directories.
- Preserve existing high-context files unless the user explicitly approved a rewrite; add pointers or scoped complements instead of normalizing names.
- Pair every prohibition with the concrete alternative: source of truth, helper, generator, command, or verification surface.

## Decision Protocol

- For non-trivial engineering work, complete P1/P2/P3 before design decisions or code edits: P1 map the real system boundary, P2 trace one concrete data/control path, and P3 state the design rationale and invariant being preserved.
- For planning requests, produce one decision-complete recommendation with scope, non-scope, tradeoffs, tests, rollback/failure handling, and the most fragile assumption; do not implement until the user approves.
- If the user says `implement this plan`, first check for obvious repo drift, then execute the approved plan without re-litigating the direction.
- For bug hunts, trace the failing path and name the root cause before changing code.
- For bundles of requests, classify items before accepting scope; do not treat every item as automatic implementation work.
- Do not add fallback, compatibility, or "best effort" product code that re-derives an authority's semantics (LLM/provider/external/user-input) with local rules, regexes, or shadow parsers; fail closed with a clear error unless the current task or a human-approved migration/release contract explicitly requires that path.

## Execution And Verification

- Prefer existing repo patterns, scripts, and standard-library/platform features before adding dependencies, files, or abstractions.
- Preserve user-authored files; do not overwrite existing `CLAUDE.md` or `AGENTS.md` except when explicitly applying an approved scaffold or syncing the controlled architecture block.
- After substantive changes, run focused checks for the touched area plus `bash scripts/check-task-sync.sh` and `bash scripts/check-task-workflow.sh --strict` when those scripts exist.
- Report what changed, why it was the smallest coherent change, verification evidence, and any concrete residual risk.
