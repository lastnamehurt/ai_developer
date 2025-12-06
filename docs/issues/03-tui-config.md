# feat: TUI config editor for profiles

## Summary
- Build a Textual-based TUI to edit profile configuration.
- Toggle MCP servers, edit env bindings, and preview launch settings.
- Support keyboard and mouse interactions.

## Acceptance Criteria
- User can open TUI (`ai config` or similar), toggle MCP servers, adjust env bindings, and save.
- Validation warnings shown before save (missing required env, invalid values).
- TUI displays server descriptions and current active profile.

## Tasks
- Scaffold Textual app with panels for profile selection, MCP list, env vars, preview.
- Wire to profile manager to read/write profile JSONs.
- Add validation layer and confirmation dialogs.
- Provide non-interactive smoke test (launchable without crash in CI).
