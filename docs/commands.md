# AI Developer — Commands Worksheet

A practical workflow guide for engineers using the `ai` CLI

Use this worksheet to quickly learn common workflows: project setup, profile switching, MCP management, tool launching, debugging, onboarding, and code review.

---

## 1. Project Quickstart & Setup

### Create a new .aidev config for a repo

```bash
ai setup
```

### Run project auto-detection to recommend a profile

```bash
ai quickstart
```

**Outputs:**
- Detected stack (JS, Python, Docker, K8s, etc.)
- Recommended profile (web, infra, pair-programmer, etc.)
- Optional initialization step

### Apply the recommended profile

```bash
ai use <profile-name>
```

### Initialize aidev in current project

```bash
ai init
```

### Back up global & project config

```bash
ai backup
```

---

## 2. Profiles: Switch, Inspect, Customize

### List all available profiles

```bash
ai profile list
```

### Switch the active profile

```bash
ai use code-surgeon
```

### Show current profile details

```bash
ai profile show
```

### Show current status (active profile and config)

```bash
ai status
```

### Reset to the default profile

```bash
ai use default
```

---

## 3. MCP Server Management

### List installed and available MCP servers

```bash
ai mcp list
```

### Search for MCP servers

```bash
ai mcp search <keyword>
```

### Install an MCP server

```bash
ai mcp install <server-name>
```

### Enable an MCP server for your profile

```bash
ai mcp enable <server-name>
```

### Disable an MCP server

```bash
ai mcp disable <server-name>
```

### View MCP server details

```bash
ai mcp show <server-name>
```

### Test MCP server connectivity

```bash
ai mcp test <server-name>
```

---

## 4. Launching Tools (Claude, Cursor, Codex, Gemini)

### Launch any supported AI tool with the active profile

```bash
ai <tool-name>
```

**Examples:**

```bash
ai claude
ai cursor
ai codex
ai gemini
```

This automatically:
- Injects the active profile
- Writes correct MCP config for that tool
- Loads enabled MCP servers
- Launches the tool in the correct mode

### Launch with a specific profile (one-time override)

```bash
ai cursor --profile infra
ai claude --profile debugger
```

### Pass additional args to the tool

```bash
ai cursor . --flag
ai codex --help
```

---

## 5. Environment & Variables

### List environment variables managed by aidev

```bash
ai env list
```

### Set a variable globally

```bash
ai env set API_KEY 12345
```

### Set a variable only for this repo

```bash
ai env set LOCAL_TOKEN abcdef --local
```

### Get a variable value

```bash
ai env get API_KEY
```

### Remove a variable

```bash
ai env unset API_KEY
```

### Diagnose env issues (missing tokens, conflicting values)

```bash
ai doctor
```

---

## 6. Code Review & Analysis Workflows

### Run code review on staged changes

```bash
ai review --staged
```

### Review an entire repo

```bash
ai review --all
```

### Review specific files or directories

```bash
ai review src/components
ai review src/auth/login.py
```

### Use a specific provider

```bash
ai review --provider codex --staged
```

---

## 7. Debugging / Diagnosis Workflows

### Analyze logs & failures with debugger profile

```bash
ai use debugger
ai claude
```

### Validate that tool integrations are configured correctly

```bash
ai doctor
```

### Check system health and configuration

```bash
ai status
```

---

## 8. Onboarding a New Engineer

### Set onboarding profile

```bash
ai use onboarding
```

### Launch Claude with repo-aware instructions

```bash
ai claude
```

Ask Claude:
> "Give me an architectural overview of this repo. What are the key modules, boundaries, and common workflows?"

---

## 9. Codebase Navigation & Refactoring

### Switch to power tools for complex codebase work

```bash
ai use code-surgeon
```

### Use AI to analyze dependencies and architecture

```bash
ai claude
```

Ask:
> "Show me everything that depends on the billing module. Identify unsafe edges."

Or:
> "Help me refactor this component to follow the repository's architecture patterns."

---

## 10. API Engineering Workflows

### Use API engineer profile

```bash
ai use api-engineer
```

### Launch with database access enabled

```bash
ai claude
```

Ask:
> "Generate an updated API spec based on the definitions in /services/users."

Or:
> "Review these REST endpoints for consistency and best practices."

---

## 11. DevOps / CI/CD Workflows

### Use DevOps profile

```bash
ai use devops
```

### Inspect Dockerfiles and Kubernetes configs

```bash
ai claude
```

Ask:
> "Explain the build layers and identify opportunities for caching or size reduction."

Or:
> "Review the Kubernetes deployment configuration for security best practices."

---

## 12. Global Maintenance

### Check aidev health and fix issues

```bash
ai doctor
```

### Restore from backup

```bash
ai restore
```

### Create backup

```bash
ai backup
```

---

## Bonus: Daily Workflows Cheat Sheet

| Workflow | Command |
|----------|---------|
| Daily coding | `ai use pair-programmer && ai claude` |
| Refactoring | `ai use code-surgeon && ai claude` |
| Debugging prod issues | `ai use debugger && ai claude` |
| API design | `ai use api-engineer && ai claude` |
| Frontend work | `ai use frontend-ui && ai cursor` |
| Testing | `ai use testing-guru && ai claude` |
| Reviewing a PR | `ai review --staged` |
| New repo setup | `ai quickstart` |
| Fix configs | `ai doctor` |

---

## Profile Reference

aidev comes with several built-in profiles optimized for different workflows:

- **pair-programmer** - Everyday coding, refactoring, test generation
- **debugger** - Deep debugging with K8s, logs, and git history
- **security** - Sandboxed security analysis
- **onboarding** - Guided codebase exploration
- **code-surgeon** - Large codebase refactoring and architecture work
- **api-engineer** - API design, testing, and validation
- **frontend-ui** - Component analysis and UI framework support
- **testing-guru** - Test coverage and quality analysis
- **devops** - CI/CD, containers, and infrastructure
- **web** - Full-stack web development (alias: default)
- **qa** - QA and testing workflows
- **infra** - Infrastructure and DevOps

See [docs/profiles.md](./profiles.md) for detailed profile documentation.

---

## Tips & Best Practices

### Profile Workflow

1. Start your day by selecting the right profile for your work
2. Keep the profile active for the entire work session
3. Switch profiles when context-switching between tasks

### Environment Variables

- Store sensitive tokens in `~/.aidev/.env` (global)
- Use project-specific `.aidev/.env` for repo-specific configs
- Use `ai env set --local` to keep credentials out of version control

### MCP Servers

- Enable only the MCP servers you need for your current profile
- Use `ai mcp test` to verify server connectivity before launching tools
- Run `ai doctor` if you experience connectivity issues

### Tool Launching

- Always launch tools via `ai <tool>` to get proper MCP configuration
- Use `--profile` flag for one-off profile overrides
- The current directory is automatically used as the workspace

---

## Getting Help

### View help for any command

```bash
ai --help
ai profile --help
ai mcp --help
ai env --help
```

### Learn interactively

```bash
ai learn
```

### Check documentation

- [Main README](../README.md)
- [Profile Catalog](./profiles.md)
- [GitHub Issues](https://github.com/lastnamehurt/ai_developer/issues)

---

For more information, visit the [project repository](https://github.com/lastnamehurt/ai_developer).
