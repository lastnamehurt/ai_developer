# AI Developer – Recommended Profiles Catalog

A curated set of MCP-driven AI profiles designed for real-world software engineers.

## Overview

Profiles in AI Developer (aidev) define the behavior, capabilities, and access level of your AI tools (Claude, Cursor, Codex, Gemini, etc.).
They enable engineers to instantly switch the AI's role — from pairing partner to debugger to codebase navigator — with a single command:

```bash
ai use <profile-name>
```

This document introduces a set of high-value profiles designed for professional software engineers across backend, frontend, DevOps, and complex codebase environments.

## Profiles

### 1. Pair Programmer

**Purpose:** Everyday coding support — refactoring, test generation, architecture suggestions, iterative dev loops.

**Ideal for:** Full-stack, backend, frontend, DX engineers.

**Features:**
- High-context file ingestion
- Git + filesystem access
- Memory bank for context persistence
- Optimized for continuous interaction with the IDE agent

**Usage:**
```bash
ai use pair-programmer
```

---

### 2. Debugger / Bug Hunter

**Purpose:** Fast root-cause analysis using logs, events, diffs, and repo search.

**Ideal for:** Backend, SRE, platform engineers.

**Features:**
- Access to Kubernetes events
- Git blame & search
- Code context analysis
- Debug mode enabled

**Usage:**
```bash
ai use debugger
```

---

### 3. Security Engineer

**Purpose:** Safe analysis of codebases without risk of leaking sensitive context.

**Ideal for:** Security teams, compliance environments.

**Features:**
- No outbound HTTP from MCP tools
- Static analysis focus
- Sandboxed environment
- No environment-sensitive ingestion (tokens, secrets, CI configs)

**Usage:**
```bash
ai use security
```

---

### 4. Onboarding

**Purpose:** Provide a guided tour through an unfamiliar codebase.

**Ideal for:** New hires, consultants, dev teams entering large projects.

**Features:**
- Repo exploration
- Search and "what owns this?" lookup
- Web search capability for documentation
- Plays well with Git and filesystem discovery

**Usage:**
```bash
ai use onboarding
```

---

### 5. Code Surgeon

**Purpose:** Understand, refactor, and work safely inside large complex codebases.

**Ideal for:** Rails / Django / Laravel applications, large monoliths, complex architectures.

**Features:**
- Global search capabilities
- Git blame + code lineage
- Context persistence via memory bank
- Architectural refactoring support

**Usage:**
```bash
ai use code-surgeon
```

---

### 6. API Engineer

**Purpose:** Build, test, evolve, and document APIs quickly.

**Ideal for:** Backend engineers, microservice teams, platform API teams.

**Features:**
- Database access (PostgreSQL)
- HTTP testing capabilities
- Repo navigation
- API design and validation

**Usage:**
```bash
ai use api-engineer
```

---

### 7. Frontend UI/UX Engineer

**Purpose:** Analyze component hierarchies, CSS scopes, bundle structure, UI behaviors.

**Ideal for:** React/Vue/Svelte engineers.

**Features:**
- Component analysis
- E2E testing support with Cypress
- Frontend search and refactor suggestions
- Git integration for tracking UI changes

**Usage:**
```bash
ai use frontend-ui
```

---

### 8. Testing Guru

**Purpose:** Improve and reason about complex testing setups.

**Ideal for:** QA, test platform, reliability engineers.

**Features:**
- E2E testing with Cypress integration
- Test coverage analysis
- Failure pattern identification
- Git integration for test history

**Usage:**
```bash
ai use testing-guru
```

---

### 9. DevOps / Build Engineer

**Purpose:** Understand build systems, CI pipelines, Docker/K8s interactions.

**Ideal for:** DevOps, platform engineers.

**Features:**
- Kubernetes cluster access
- Container and orchestration support
- Build dependency discovery
- CI/CD pipeline analysis

**Usage:**
```bash
ai use devops
```

---

## Using Profiles

### Switching Profiles

To switch between profiles in your current project:

```bash
ai use <profile-name>
```

### Listing Available Profiles

To see all available profiles:

```bash
ai profile list
```

### Creating Custom Profiles

You can create your own custom profiles by extending existing ones. See the [main README](../README.md) for more information on profile customization.

### Profile Inheritance

Profiles can extend other profiles using the `extends` field. This allows you to build on top of existing profiles and customize them for your specific needs.

Example:
```json
{
  "name": "my-custom-profile",
  "description": "Custom profile for my team",
  "extends": "pair-programmer",
  "mcp_servers": [
    {
      "name": "gitlab",
      "enabled": true
    }
  ]
}
```

## Environment Variables

Most profiles require certain environment variables to be set. Common ones include:

- `GITHUB_TOKEN` - For GitHub integration
- `GITLAB_PERSONAL_ACCESS_TOKEN` - For GitLab integration
- `KUBECONFIG` - For Kubernetes access
- `POSTGRES_URL` - For database access

Set these in your global `~/.aidev/.env` file or project-specific `.aidev/.env` file.

## Contributing

Have a profile idea? Submit a PR with your profile definition in `examples/profiles/` and add it to this catalog!
