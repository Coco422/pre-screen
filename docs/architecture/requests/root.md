# Architecture Queue Card: root

> **Status**: Pending
> **Detected**: 2026-07-07T19:01:21+0800
> **Updated**: 2026-07-07T19:28:54+0800
> **Severity**: high
> **Change Type**: data-or-deploy
> **File**: `docker-compose.yml`
> **Functional Block**: `root`
> **Capability ID**: `root`
> **Matched Prefix**: `root`
> **Architecture Domain**: `root`
> **Architecture Capability**: `_root`
> **Architecture Module**: `docs/architecture/index.md`
> **Workstream Directory**: `tasks/workstreams/root/_root`
> **Contract Files**: `none`, `none`
> **Contract Sync Required**: false
> **Spawn Recommended**: true
> **Open Edits**: 2

## Required Follow-up

- Read root `AGENTS.md` / `CLAUDE.md`.
- If functional block is not `root`, read its local `AGENTS.md` / `CLAUDE.md`.
- Decide whether this change affects module boundaries, entrypoints, dependency rules, runtime paths, or verification commands.
- For substantial changes, write a snapshot under `docs/architecture/snapshots/`.
- When a visual explains the boundary better than prose, add or update a Mermaid fenced block in the relevant architecture module or snapshot Markdown first; that Markdown is the semantic source for LLM readers.
- When a human-readable rendering is useful, generate a matching `$mermaid` architecture HTML file under `docs/architecture/diagrams/` and link it back to the Markdown semantic source.
- Treat `mermaid` as an external installed skill dependency at `~/.codex/skills/mermaid`; do not copy, vendor, or inline its templates into this repo.
- If this starts or advances durable execution, run `repo-harness run workstream-sync ensure --block "root" --request "docs/architecture/requests/root.md"`.
- After the snapshot or diagram is produced, run `repo-harness run context-contract-sync sync-latest` so the local architecture contract block links to the latest artifacts.

## Touched Files

| Last Event | Severity | Change Type | File |
| --- | --- | --- | --- |
| 2026-07-07T19:28:54+0800 | high | data-or-deploy | `docker-compose.yml` |
| 2026-07-07T19:02:02+0800 | medium | boundary-or-config | `apps/web/vite.config.ts` |

## Event Fields

```json
{
  "ts": "2026-07-07T19:28:54+0800",
  "file_path": "docker-compose.yml",
  "severity": "high",
  "functional_block": "root",
  "capability_id": "root",
  "matched_prefix": "root",
  "architecture_domain": "root",
  "architecture_capability": "_root",
  "architecture_module": "docs/architecture/index.md",
  "workstream_dir": "tasks/workstreams/root/_root",
  "contract_agents": "",
  "contract_claude": "",
  "change_type": "data-or-deploy",
  "request_file": "docs/architecture/requests/root.md",
  "spawn_recommended": true,
  "contract_sync_required": false
}
```
