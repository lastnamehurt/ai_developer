# Plan to Add New MCP Servers

Based on the latest research, this document outlines the plan to add two new high-value MCP servers to `examples/mcp-registry.json`.

---

## Proposed Additions

### 1. Add Snyk MCP Server

- **Reasoning:** Snyk is a leader in developer security. The official Snyk CLI now includes a built-in MCP server, providing a powerful and trusted tool for vulnerability scanning directly within AI workflows.
- **Action:** Add the following JSON object to the registry array.

```json
{
  "name": "snyk",
  "command": "snyk",
  "args": ["mcp", "--experimental"],
  "description": "Scans for vulnerabilities in code and dependencies using the Snyk CLI.",
  "author": "Snyk",
  "repository": "https://github.com/snyk/cli",
  "version": "1.0.0",
  "install": {
    "type": "npm",
    "command": "npm install -g snyk"
  },
  "configuration": {
    "required": ["SNYK_TOKEN"],
    "optional": []
  },
  "tags": ["security", "devsecops", "vulnerability", "scanner"]
}
```

### 2. Add Omnisearch MCP Server

- **Reasoning:** This server is a significant upgrade over any single web search provider. It unifies over 7 different search, content processing, and AI response services (Tavily, Perplexity, Kagi, Brave, etc.) into a single, powerful tool. It will replace the need for the old, broken `web-search` entry.
- **Action:** Add the following JSON object to the registry array.

```json
{
  "name": "omnisearch",
  "command": "mcp-omnisearch",
  "description": "Unified access to multiple search, content processing, and AI response services.",
  "author": "spences10",
  "repository": "https://github.com/spences10/mcp-omnisearch",
  "version": "0.0.18",
  "install": {
    "type": "npm",
    "command": "npm install -g mcp-omnisearch"
  },
  "configuration": {
    "required": [],
    "optional": [
      "TAVILY_API_KEY", 
      "PERPLEXITY_API_KEY", 
      "KAGI_API_KEY", 
      "JINA_AI_API_KEY", 
      "BRAVE_API_KEY", 
      "GITHUB_API_KEY", 
      "EXA_API_KEY", 
      "FIRECRAWL_API_KEY"
    ]
  },
  "tags": ["search", "web", "ai", "research", "omni"]
}
```
