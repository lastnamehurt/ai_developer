# feat: streamline built-in profiles and profile switch command

## Summary
- Finalize built-in profiles (web, qa, infra; keep work as custom/extension).
- Provide fast profile switch command (`ai use <profile>`) and status (`ai status`).
- Show active env requirements and MCP servers in status.

## Acceptance Criteria
- `ai use <profile>` switches in <100ms (no perceptible delay).
- `ai status` shows profile name, enabled MCP servers, and required env vars with set/missing indicators.
- Legacy profiles are deprecated/hidden from default list; work profile remains available as custom or extension.

## Tasks
- Define web/qa/infra profile JSONs and retire old ones from built-ins.
- Implement `ai use` command and persistence to project/global state.
- Enhance `ai status` output with env requirements (per profile) and MCP summary.
- Update docs/help to reflect new profile set.
