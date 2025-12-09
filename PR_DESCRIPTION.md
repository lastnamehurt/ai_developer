# Add Developer Experience Engineer workflows and improve workflow system

## Summary

This PR adds 8 new workflows specifically designed for Developer Experience Engineers and improves the workflow system to ensure built-in workflows are always available globally.

## Changes

### New Workflows (8)

Added the following Developer Experience Engineer workflows to `src/aidev/configs/workflows.yaml`:

1. **`onboarding_guide`** - Create comprehensive onboarding guides for new developers
2. **`error_message_improver`** - Analyze and improve error message clarity and actionability
3. **`migration_guide`** - Create migration guides for breaking changes, API updates, or major version upgrades
4. **`api_doc_improver`** - Improve API documentation by analyzing code, existing docs, and developer feedback
5. **`developer_feedback_analyzer`** - Analyze developer feedback, surveys, or support tickets to identify pain points
6. **`troubleshooting_guide`** - Create troubleshooting guides from bug reports, error logs, or support tickets
7. **`quickstart_creator`** - Create quickstart or getting started guides by analyzing project structure
8. **`ci_cd_dx_improver`** - Improve CI/CD developer experience by analyzing pipeline failures and feedback

### Workflow System Improvements

- **Template + Project Merge**: Workflows now load from both the template (always available) and project-specific files (for overrides/extensions)
  - Template workflows ship with the app and are globally accessible
  - Project workflows can override or extend template workflows
  - Ensures built-in workflows are always available, even in projects without a `.aidev/workflows.yaml` file

- **Enhanced Workflow List Command**:
  - Added support for `ai workflow list` (in addition to existing `--list` flag)
  - Formatted workflow list as Rich table for better readability
  - Workflows sorted alphabetically for easier scanning

### Documentation

- Added comprehensive documentation in `docs/dx-engineer-workflows.md`:
  - Purpose and usage for each workflow
  - Example commands and inputs
  - Best practices and customization options
  - Troubleshooting guide

### Other Improvements

- Updated `memory-bank.json` to use `@latest` version tag
- Updated `tools.py` to treat Cursor as interactive CLI tool
- Minor updates to `supported-tools.json`

## Why

Developer Experience Engineers need workflows that focus on:
- Creating clear, actionable documentation
- Improving developer-facing error messages
- Analyzing developer feedback to identify pain points
- Creating migration guides for breaking changes
- Building self-service troubleshooting resources

These workflows automate common DX tasks and help maintain consistent, high-quality developer experience across projects.

## Testing

1. **List workflows**:
   ```bash
   ai workflow list
   # or
   ai workflow --list
   ```
   Should show all 13 workflows (5 existing + 8 new) in a formatted table.

2. **Test new workflow**:
   ```bash
   ai workflow onboarding_guide "Create onboarding guide for new backend engineers"
   ```

3. **Verify template workflows are available**:
   - In a project without `.aidev/workflows.yaml`, workflows should still be available
   - Template workflows should merge with project workflows if both exist

4. **Test workflow loading**:
   ```bash
   python -c "from aidev.workflow import WorkflowEngine; engine = WorkflowEngine(); w, _ = engine.load_workflows(); print(f'Found {len(w)} workflows')"
   ```
   Should show 13 workflows.

## Files Changed

- `src/aidev/configs/workflows.yaml` - Added 8 new workflows
- `src/aidev/workflow.py` - Improved workflow loading (template + project merge)
- `src/aidev/cli.py` - Enhanced workflow list formatting and added `list` command support
- `docs/dx-engineer-workflows.md` - New comprehensive documentation (486 lines)
- `src/aidev/configs/mcp-servers/memory-bank.json` - Updated to `@latest`
- `src/aidev/configs/supported-tools.json` - Minor update
- `src/aidev/tools.py` - Treat Cursor as interactive CLI

## Related

- Documentation: `docs/dx-engineer-workflows.md`
- Workflow system: `src/aidev/workflow.py`
- Workflow definitions: `src/aidev/configs/workflows.yaml`
