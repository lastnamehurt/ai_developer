# chore: integration tests for quickstart/profile/tui flows

## Summary
- Extend integration coverage beyond MCP config generation.
- Add end-to-end tests for quickstart, profile switching, and MCP config generation.
- Add non-interactive smoke tests for TUI entry points where possible.

## Acceptance Criteria
- Integration suite covers quickstart -> profile set -> MCP config generation happy path.
- Profile switch and status commands verified in tests.
- TUI entry points can be invoked in a non-interactive smoke test without crashing.

## Tasks
- Add fixtures for sample JS/Python projects for quickstart tests.
- Write integration tests for profile switching and MCP config generation.
- Add smoke test that launches TUI in headless mode (as feasible) to ensure no import/runtime errors.
