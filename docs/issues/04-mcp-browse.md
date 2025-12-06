# feat: MCP registry browse/install/test flow

## Summary
- Implement MCP registry client and interactive browser.
- Allow search/filter, install/uninstall servers, and connectivity testing.
- Suggest profile compatibility and update active profile on install.

## Acceptance Criteria
- Can browse and search registry entries; handles offline mode gracefully.
- Install/uninstall flows succeed and update active profile when chosen.
- Connectivity test reports success/failure with actionable hints.

## Tasks
- Add registry client (cached) with search/filter.
- Build TUI/CLI browse command (list with descriptions, install buttons).
- Implement install/uninstall commands and profile integration toggles.
- Add `ai mcp test <server>` with friendly output.
