# Architecture Index

> Umbrella architecture ledger for current boundaries, drift requests, snapshots, and diagrams.

## Current Snapshot

- Latest snapshot: [2026-07-09 MVP demo gateway](snapshots/2026-07-09-mvp-demo-gateway.md)
- Semantic diagram source: snapshot 内 topology（Mermaid 可后续补）
- Latest human diagram: (none yet)
- Active cutover plan: `plans/plan-20260709-production-cutover.md`

## Architecture Drift Flow

- `repo-harness run architecture-queue` records architecture-sensitive edits as requests.
- `repo-harness run archive-architecture-request` archives handled requests after an agent records the resolution status and linked artifacts.
- `repo-harness run context-contract-sync` keeps only the controlled architecture block in functional-block `AGENTS.md` and `CLAUDE.md` files aligned.
- `repo-harness run workstream-sync` keeps durable multi-session progress under `tasks/workstreams/<domain>/<capability>/` and projects only pointers into local contracts.
- Semantic architecture diagrams live as Mermaid fenced blocks in the relevant module or snapshot Markdown.
- Human-readable architecture diagrams are optional `mermaid` HTML files in `docs/architecture/diagrams/` and should link back to the Markdown semantic source.

## Pending Requests

<!-- BEGIN ARCHITECTURE PENDING REQUESTS -->
- [ ] 2026-07-07T19:28:54+0800 [high] `docker-compose.yml` -> [root](requests/root.md)
<!-- END ARCHITECTURE PENDING REQUESTS -->
