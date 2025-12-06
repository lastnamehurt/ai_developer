# MCP Server Setup Guide

Detailed installation and configuration instructions for all MCP servers.

## GitHub MCP Server

The official GitHub MCP server provides deep integration with GitHub APIs.

### Installation Options

#### Option 1: Binary (Recommended)
```bash
# Download latest release
# From: https://github.com/github/github-mcp-server/releases
# Extract and add to PATH

# Or with our tool
ai mcp install github
```

#### Option 2: Docker
```bash
# Use the Docker variant
ai mcp install github-docker

# Requires Docker Desktop running
```

#### Option 3: Remote (HTTP)
```bash
# Connect to Anthropic's hosted endpoint
# Requires adding HTTP transport support to aidev (future feature)
```

### Configuration

**Binary**:
```json
{
  "command": "github-mcp-server",
  "args": ["stdio"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token"
  }
}
```

**Docker**:
```json
{
  "command": "docker",
  "args": ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN", "ghcr.io/github/github-mcp-server"],
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token"
  }
}
```

### Requirements

1. **GitHub Personal Access Token (PAT)**
   - Create at: https://github.com/settings/tokens
   - Required scope: `repo`
   - Set in `~/.aidev/.env`:
     ```bash
     GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
     ```

2. **Binary Installation** (for non-Docker setup)
   - Download from releases page
   - Add to PATH
   - Verify: `github-mcp-server --version`

3. **Docker Installation** (for Docker setup)
   - Docker Desktop must be running
   - Image: `ghcr.io/github/github-mcp-server`

### Usage

```bash
# Set your token
ai env set GITHUB_PERSONAL_ACCESS_TOKEN ghp_your_token

# Use in a profile
ai cursor --profile fullstack

# Or use default-personal profile (includes GitHub)
ai cursor --profile default-personal
```

### Profiles Using GitHub

- `fullstack` - Web development
- `default-personal` - Personal projects
- `web-dev` - Full-stack web dev (example)

## GitLab MCP Server

GitLab integration with CI/CD pipelines, wikis, and milestones.

### Installation

```bash
# Auto-installed via npx
ai mcp install gitlab
```

Or manually:
```bash
npm install -g @zereight/mcp-gitlab
```

### Configuration

```json
{
  "command": "npx",
  "args": ["-y", "@zereight/mcp-gitlab"],
  "env": {
    "GITLAB_PERSONAL_ACCESS_TOKEN": "glpat_your_token",
    "GITLAB_URL": "https://gitlab.com",
    "GITLAB_API_URL": "https://gitlab.com/api/v4",
    "GITLAB_READ_ONLY_MODE": "false",
    "USE_GITLAB_WIKI": "true",
    "USE_MILESTONE": "true",
    "USE_PIPELINE": "true"
  }
}
```

### Requirements

1. **GitLab Personal Access Token**
   - Create at: https://gitlab.com/-/profile/personal_access_tokens
   - Required scopes: `api`, `read_repository`, `write_repository`
   - Set in `~/.aidev/.env`:
     ```bash
     GITLAB_PERSONAL_ACCESS_TOKEN=glpat_your_token_here
     GITLAB_URL=https://gitlab.checkrhq.net  # For self-hosted
     GITLAB_API_URL=https://gitlab.checkrhq.net/api/v4
     ```

2. **Read-Only Mode** (for QA/review workflows)
   ```bash
   GITLAB_READ_ONLY_MODE=true
   ```

### Usage

```bash
# Set your token
ai env set GITLAB_PERSONAL_ACCESS_TOKEN glpat_your_token
ai env set GITLAB_URL https://gitlab.your-company.com

# Use in a profile
ai cursor --profile devops
ai cursor --profile default-work
```

### Profiles Using GitLab

- `devops` - Infrastructure work
- `default-work` - Work projects
- `devops-gitlab` - DevOps with GitLab CI/CD (example)
- `qa-gitlab` - QA with read-only access (example)

## Git MCP Server

Basic git operations (local repos).

### Installation

```bash
# Install via cargo
cargo install git-mcp-server
```

### Configuration

```json
{
  "command": "git-mcp-server",
  "args": []
}
```

### Usage

Included in all profiles by default. Provides local git operations without requiring GitHub/GitLab APIs.

## Kubernetes MCP Server

Kubernetes cluster management.

### Installation

```bash
# Install via cargo
cargo install k8s-mcp-server
```

### Configuration

```json
{
  "command": "k8s-mcp-server",
  "args": ["--mode", "stdio"],
  "env": {
    "KUBECONFIG": "${HOME}/.kube/config"
  }
}
```

### Requirements

1. **kubectl installed** and configured
2. **KUBECONFIG** pointing to your cluster config

### Usage

```bash
# Use default kubeconfig
ai cursor --profile devops

# Or specify custom kubeconfig
ai env set KUBECONFIG /path/to/my/kubeconfig
```

## Cypress MCP Server

End-to-end testing integration.

### Installation

```bash
# Clone and install locally
git clone https://github.com/cypress-io/cypress-mcp-server ~/.local/share/cypress-mcp-server
cd ~/.local/share/cypress-mcp-server
npm install
```

### Configuration

```json
{
  "command": "node",
  "args": ["${HOME}/.local/share/cypress-mcp-server/src/index.js"]
}
```

### Usage

```bash
# Use in QA profiles
ai cursor --profile qa-gitlab
```

## Memory Bank MCP Server

Persistent memory across AI sessions.

### Installation

```bash
# Auto-installed via npx
ai mcp install memory-bank
```

### Configuration

```json
{
  "command": "npx",
  "args": ["-y", "@allpepper/memory-bank-mcp"],
  "env": {
    "MEMORY_BANK_ROOT": "${HOME}/.aidev/memory-banks"
  }
}
```

### Usage

Memory banks are organized per profile/project:

```bash
# Personal projects
MEMORY_BANK_ROOT=~/.aidev/memory-banks/personal

# Work projects
MEMORY_BANK_ROOT=~/.aidev/memory-banks/work

# Research
MEMORY_BANK_ROOT=~/.aidev/memory-banks/research
```

## DuckDuckGo Search

Web search capabilities.

### Installation

```bash
# Install via uvx (Python)
uv tool install duckduckgo-mcp-server
```

Or with pip:
```bash
pip install duckduckgo-mcp-server
```

### Configuration

```json
{
  "command": "uvx",
  "args": ["duckduckgo-mcp-server"]
}
```

### Usage

```bash
# Use in research profiles
ai cursor --profile researcher
ai cursor --profile researcher-advanced
```

## Atlassian (JIRA/Confluence)

Remote MCP server for Atlassian suite.

### Configuration

```json
{
  "command": "npx",
  "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
}
```

### Requirements

- Atlassian account
- Authentication handled by remote server

### Usage

```bash
# Use in work profiles
ai cursor --profile default-work
ai cursor --profile devops
```

## PostgreSQL

Database access and queries.

### Installation

```bash
# Auto-installed via npx
ai mcp install postgres
```

### Configuration

```json
{
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres"],
  "env": {
    "POSTGRES_URL": "postgresql://localhost:5432/mydb"
  }
}
```

### Usage

```bash
# Set connection string
ai env set POSTGRES_URL postgresql://user:pass@localhost:5432/dbname

# Use in data/fullstack profiles
ai cursor --profile data
ai cursor --profile fullstack
```

## Quick Reference

| Server | Install Command | Env Var Required |
|--------|----------------|------------------|
| github | Download binary | GITHUB_PERSONAL_ACCESS_TOKEN |
| gitlab | `npm install -g @zereight/mcp-gitlab` | GITLAB_PERSONAL_ACCESS_TOKEN |
| git | `cargo install git-mcp-server` | None |
| k8s | `cargo install k8s-mcp-server` | KUBECONFIG (optional) |
| cypress | Manual git clone | None |
| memory-bank | Auto (npx) | MEMORY_BANK_ROOT (optional) |
| duckduckgo | `uv tool install` | None |
| atlassian | Auto (npx remote) | None (remote auth) |
| postgres | Auto (npx) | POSTGRES_URL |

## Troubleshooting

### Server Not Found

```bash
# Check if server is installed
ai mcp list

# Verify config exists
cat ~/.aidev/config/mcp-servers/server-name.json

# Test connectivity
ai mcp test server-name
```

### Permission Errors

```bash
# GitHub/GitLab: Check token scopes
# https://github.com/settings/tokens (GitHub)
# https://gitlab.com/-/profile/personal_access_tokens (GitLab)

# Verify token is set
ai env get GITHUB_PERSONAL_ACCESS_TOKEN
ai env get GITLAB_PERSONAL_ACCESS_TOKEN
```

### Docker Issues

```bash
# Check Docker is running
docker ps

# Test image manually
docker run -it --rm ghcr.io/github/github-mcp-server --version
```

---

**Next**: See [examples/profiles/](../examples/profiles/) for ready-to-use profile configurations.
