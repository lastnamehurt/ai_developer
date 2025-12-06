# feat: actionable error messaging and preflight checks

## Summary
- Centralize error handling with actionable guidance.
- Add preflight checks for required env vars, binaries, and configs before launching tools.
- Provide suggested fixes with commands/links where possible.

## Acceptance Criteria
- Launching without required env keys prints clear instructions (e.g., `ai env set ...`) and links.
- Missing binary/config errors use the central helper; no raw tracebacks in normal paths.
- Preflight can be invoked standalone (e.g., `ai doctor` additions) and runs before tool launch.

## Tasks
- Implement error helper utilities and message catalog.
- Add preflight hooks to tool launch paths.
- Extend `ai doctor` (or new command) to include env/binary/config validation.
- Add tests for common failure scenarios.
