# Final Plan to Fix Broken MCP Entries

This document outlines the final plan to fix broken entries in the `examples/mcp-registry.json` file, based on extensive verification.

## Summary of Findings

- The registry contains 17 entries with broken repository URLs.
- A correct URL was found for the `k8s` server.
- The `memory` server was found to have been moved to the `modelcontextprotocol/servers` monorepo.
- No new, working URLs could be found for the other 15 broken entries.
- The application's data model does not support a "note" or "disabled" field. The cleanest way to handle defunct entries is to remove them.

---

## Proposed Changes to `examples/mcp-registry.json`

### 1. Entries to FIX

The following entries will be updated with correct information:

- **`k8s`**:
    - **Change:** Update the `repository` field.
    - **From:** `"https://github.com/kubernetes-mcp/k8s-mcp-server"`
    - **To:** `"https://github.com/aws-samples/k8s-mcp-server"`

- **`memory`**:
    - **Change 1:** Update the `repository` field.
    - **From:** `"https://github.com/aidev/mcp-memory"`
    - **To:** `"https://github.com/modelcontextprotocol/servers"`
    - **Change 2:** Update the `install.command` field to reflect the new package structure in the monorepo.
    - **From:** `"npm install -g @aidev/mcp-server-memory"`
    - **To:** `"npm install -g @modelcontextprotocol/server-memory"`

### 2. Entries to REMOVE

The following 15 entries will be **completely removed** from the JSON registry file, as they are defunct and cannot be fixed at this time:

- `gitlab`
- `redis`
- `cypress`
- `docker`
- `aws`
- `s3`
- `web-search`
- `jupyter`
- `jira`
- `slack`
- `confluence`
- `mongodb`
- `elasticsearch`
- `terraform`
- `prometheus`

---

This plan will result in a smaller, but fully functional and verified, list of MCP servers available to users of the `aidev` tool.