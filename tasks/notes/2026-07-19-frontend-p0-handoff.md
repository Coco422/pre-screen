# Frontend P0 Stabilization Handoff

> **Status**: Ready to resume; investigation only, no product code changed
> **Recorded**: 2026-07-19
> **Source**: Kimi session interrupted by provider quota
> **Branch / baseline**: `main` at `b46cbdf`
> **Active plan**: `plans/plan-20260709-production-cutover.md`

## Resume Goal

The user approved this order:

1. Restore the frontend build/test baseline.
2. Remove the admin authentication and list-loading fail-open fallbacks.
3. Complete Phase 4.4: parsing failure, AI unavailability, and Judge0 timeout must be visible and retryable.
4. Run focused frontend checks plus the repository workflow checks.
5. Only after all P0 acceptance checks pass, commit and push; then report the next-plan document location.

This note is a recovery packet, not evidence that any P0 implementation is complete.

## Verified Checkpoint

- The worktree was clean before this documentation-only handoff was written. Kimi left no uncommitted implementation changes.
- `cd apps/web && npm ls vue-pdf-embed --depth=0` reports an empty dependency tree even though `vue-pdf-embed` is declared in `package.json` and present in the npm lockfile.
- `cd apps/web && npm run build` fails in `CandidateDetailView.vue` because `vue-pdf-embed` cannot be resolved.
- `cd apps/web && npm test` currently reports:
  - 14 test files: 12 passed, 2 failed.
  - 43 tests: 41 passed, 2 failed.
  - `CandidateDetailView.spec.ts` cannot load for the same missing dependency.
  - `adminNavigation.spec.ts` contains stale expectations: it still expects `风险管理` and three placeholder destinations, while the current navigation contains seven real destinations including `考试监控` and no placeholders.
- `apps/web/src/lib/gateway.ts` contains a generic `requestJson(..., fallback)` mechanism that catches every fetch/HTTP/JSON error and returns local fallback data.
- The seven current silent fallback call sites are:
  - `loginAdmin` -> hard-coded `demo-admin-token` / `Ray HR` session.
  - `fetchAdminSession` -> the same hard-coded session.
  - `loadTasks`, `loadCandidates`, `loadPapers`, `loadResults`, `loadMonitorSessions` -> `{ items: [] }`.

## P1 / P2 / P3 Decision Frame

### P1 — Boundary

- Primary scope: `apps/web` gateway/session/list-loading behavior and the UI surfaces needed by Phase 4.4.
- Inspect backend contracts only where a real retry action or structured failure state is required.
- Do not absorb the broader lint, lockfile, bundle, dead-code, large-view, polling, or style cleanup into this P0 slice.

### P2 — Concrete Failing Paths

```text
AdminLoginView -> adminSession store -> loginAdmin -> requestJson
  -> any 401/network/JSON error -> demo admin session -> unauthorized login succeeds

Admin list view -> loadTasks/loadCandidates/loadPapers/loadResults/loadMonitorSessions
  -> API failure -> [] -> UI renders "no data" instead of an error

CandidateDetailView -> dynamic import("vue-pdf-embed")
  -> dependency absent from node_modules -> typecheck/build/test collection fail
```

Kimi's backend-contract investigation also reached these provisional conclusions; re-open the named code before implementation:

- Resume parse failures are persisted with `status="failed"` and `error_message` in the Postgres candidate/upload-job path, but the exact authoritative retry endpoint/action still needs confirmation.
- Paper generation has a persisted failed job/error path; the UI must expose it and retry through the existing generation authority instead of fabricating local state.
- Judge0 test-case timeout is a successful HTTP result with Judge0 status information (TLE commonly status id 5), while infrastructure timeout can surface as an unstructured server error. The candidate can submit again through the existing coding endpoint; there is no separate re-judge endpoint in the current contract.

### P3 — Invariant

- Authentication, backend data, AI output, parse state, and Judge0 state remain authoritative outside the frontend.
- The frontend must fail closed and show actionable errors. It must not convert authority failures into demo sessions, empty lists, local success, or shadow-parsed semantics.
- Retry actions must call a real existing backend operation. If the contract is missing, stop and make that gap explicit before inventing frontend behavior.

## Recommended Implementation Sequence

### 1. Restore the baseline

- Run `npm ci` in `apps/web` before changing dependency manifests; the first hypothesis is a stale/incomplete local install, not a missing declaration.
- Confirm `npm ls vue-pdf-embed --depth=0` resolves the package.
- Update `adminNavigation.spec.ts` to the current approved navigation and assert that no placeholder destinations remain.
- Re-run `npm test` and `npm run build`.
- Do not remove the stale `pnpm-lock.yaml` in this slice; that belongs to the later package-manager cleanup and needs explicit confirmation because it deletes a tracked file.

### 2. Make gateway/session behavior fail closed

- Remove the generic fallback return path from `requestJson` and delete `fallbackSession`.
- Require login/session responses to provide the required token/user fields; malformed success payloads should reject clearly.
- Preserve useful HTTP context in thrown errors so login and page-level error states can distinguish unauthorized access from temporary backend failure where the UI already supports it.
- Confirm the admin session store/router clears or rejects invalid sessions instead of keeping a stale authenticated state.
- Add focused tests for login 401/network failure, session recovery failure, and list API failure propagation.

### 3. Complete Phase 4.4

- Trace one real request/response path for each failure before editing UI:
  - resume parse failure and retry;
  - AI/paper generation failure and retry;
  - Judge0 timeout/infrastructure failure and resubmission.
- Reuse persisted `processing.status`, `error_message`, and Judge0 `status` fields where available.
- Ensure each affected page visibly distinguishes loading, empty, failed, and retrying states.
- Add focused component/gateway tests for the three failure paths and retry actions.

### 4. Verification and delivery gate

At minimum:

```bash
cd apps/web
npm ls vue-pdf-embed --depth=0
npm test
npm run build

cd ../..
if [ -x scripts/check-task-sync.sh ]; then bash scripts/check-task-sync.sh; fi
if [ -x scripts/check-task-workflow.sh ]; then bash scripts/check-task-workflow.sh --strict; fi
```

At this checkpoint, both repository-local check scripts are absent and `repo-harness` is not on `PATH`; report that limitation unless the next environment provides the helpers. Also run any touched backend tests if Phase 4.4 requires a backend retry/status contract change. Do not claim P0 complete, commit, or push until the checks are green or any unexecutable check is reported explicitly.

## Open Questions Before Editing

1. What is the current authoritative retry operation for a failed resume upload: re-upload, an existing retry endpoint, or a missing backend contract?
2. Which UI owns AI-unavailable recovery in the current flow: task detail, candidate detail, paper generation/list, or more than one surface?
3. Should Judge0 infrastructure errors be normalized by the gateway/backend in this P0 slice, or can the existing error response support a clear candidate-facing retry state without a contract change?

These questions should be answered from current routes/tests first. Ask the user only if the repository cannot determine the intended behavior or if a shared API contract must change.

## Audit Findings Preserved for After P0

Not part of the approved immediate implementation scope:

- No lint/format command or independent typecheck script.
- Both npm and pnpm lockfiles are tracked; Docker currently uses npm.
- Dev proxy and frontend env typing/example configuration need cleanup.
- Element Plus is globally imported; bundle/style strategy is unresolved.
- Roughly 500 lines of likely dead/redirected frontend views remain.
- `gateway.ts` is a large API/mapping monolith; several views use raw `fetch`; API base constants are duplicated.
- Polling, localStorage keys, styles, and tests are fragmented around the largest views.
- `docs/spec.md` still says result score correction is not wired, while Phase 4.1 and current code indicate it is implemented.

Re-triage these after P0 rather than mixing them into the stabilization commit.
