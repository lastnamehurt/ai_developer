# aidev Examples

This directory contains example configurations to help you get started with aidev.

## Directory Structure

```
examples/
├── profiles/                      # Example custom profiles
│   ├── web-dev.json              # Full-stack web development
│   ├── mobile-dev.json           # Mobile app development
│   ├── security-research.json    # Security research & pentesting
│   ├── ml-engineer.json          # Machine learning & AI
│   └── documentation-writer.json # Technical writing
│
├── project-configs/               # Example project configurations
│   ├── web-app/                  # Web application example
│   ├── mobile-app/               # Mobile app example
│   └── ml-project/               # ML project example
│
├── mcp-registry.json              # Mock MCP server registry
└── global-env-example.env         # Example global environment file
```

## Using Example Profiles

### 1. Import a Custom Profile

```bash
# Copy profile to your custom profiles directory
cp examples/profiles/web-dev.json ~/.aidev/config/profiles/custom/

# Or use the import command
ai profile import examples/profiles/web-dev.json

# List profiles to verify
ai profile list

# Use the profile
ai cursor --profile web-dev
```

### 2. Create Your Own Based on Examples

```bash
# Start with an example
cp examples/profiles/web-dev.json my-custom-profile.json

# Edit to your needs
vim my-custom-profile.json

# Import when ready
ai profile import my-custom-profile.json
```

## Example Profiles

### web-dev.json
**Use case**: Full-stack web development with modern tools

**Includes**:
- Filesystem, Git, GitHub
- PostgreSQL, Redis
- Docker

**Environment variables**:
- `GITHUB_TOKEN`, `DATABASE_URL`, `REDIS_URL`, `NODE_ENV`

### mobile-dev.json
**Use case**: React Native, iOS, and Android development

**Includes**:
- Filesystem, Git, GitHub
- Simulator access

**Environment variables**:
- `ANDROID_HOME`, `JAVA_HOME`, `EXPO_TOKEN`

### security-research.json
**Use case**: Security research and penetration testing

**Includes**:
- Web search, Memory
- Vulnerability databases

**Environment variables**:
- `SHODAN_API_KEY`, `VIRUSTOTAL_API_KEY`, `NVD_API_KEY`

### ml-engineer.json
**Use case**: Machine learning and AI development

**Includes**:
- Jupyter, Postgres
- S3, MLflow

**Environment variables**:
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `MLFLOW_TRACKING_URI`

### documentation-writer.json
**Use case**: Technical writing and documentation

**Includes**:
- Filesystem, Git, GitHub (read-only)
- Web search, Markdown lint, Spell check

**Environment variables**:
- `GITHUB_TOKEN`

## Using Example Project Configs

### Initialize a New Project

```bash
# Start a new web app
mkdir my-web-app && cd my-web-app
cp -r ../examples/project-configs/web-app/.aidev ./

# Edit the configuration
vim .aidev/config.json
vim .aidev/.env

# Launch with the project configuration
ai cursor
```

### Project Configuration Structure

Each example project has:

1. **config.json** - Project settings
   - Active profile
   - Environment overrides
   - MCP server overrides

2. **.env** - Project environment variables
   - Database URLs
   - API keys
   - Feature flags

3. **profile** - Active profile name (simple text file)

## Using the Mock MCP Registry

For development and testing:

```bash
# Point aidev to use the mock registry
export AIDEV_MCP_REGISTRY_URL="file://$(pwd)/examples/mcp-registry.json"

# Or modify the registry URL in code
# Edit: src/aidev/constants.py
# DEFAULT_MCP_REGISTRY = "file:///path/to/examples/mcp-registry.json"

# Search the registry
ai mcp search kubernetes

# Install from registry
ai mcp install kubernetes
```

### Registry Contains

- **Core servers**: filesystem, git, github, gitlab
- **Databases**: postgres, redis, mongodb, elasticsearch
- **Cloud**: aws, s3, kubernetes, docker
- **Tools**: jupyter, terraform, prometheus
- **Communication**: slack, jira, confluence
- **Research**: web-search, memory

## Setting Up Global Environment

### 1. Copy the Example

```bash
cp examples/global-env-example.env ~/.aidev/.env
```

### 2. Edit with Your Credentials

```bash
# Edit the file
vim ~/.aidev/.env

# Add your actual tokens and keys
GITHUB_TOKEN="ghp_your_real_token"
ANTHROPIC_API_KEY="sk-ant-your_real_key"
# ... etc
```

### 3. Verify

```bash
# List environment variables (secrets will be masked)
ai env list

# Get a specific variable
ai env get GITHUB_TOKEN
```

## Tips

### Organizing Profiles

Create profiles for different contexts:

```bash
# Work profile
ai profile create work --extends web-dev

# Personal projects
ai profile create personal --extends minimal

# Client work
ai profile create client-acme --extends web-dev
```

### Project Templates

Create template directories for common project types:

```bash
mkdir -p ~/templates/web-app
cp -r examples/project-configs/web-app/.aidev ~/templates/web-app/

# Use when starting new projects
cp -r ~/templates/web-app/.aidev ./
```

### Sharing with Team

Export configurations without secrets:

```bash
# Export profile
ai profile export web-dev --output team-profile.json

# Share team-profile.json with team
# Team members import:
ai profile import team-profile.json
```

### Environment Variables

Use variable expansion in configs:

```json
{
  "environment": {
    "PROJECT_ROOT": "${PWD}",
    "DATA_DIR": "${PWD}/data",
    "USER_HOME": "${HOME}"
  }
}
```

## Customization Ideas

### Create Role-Based Profiles

- `frontend` - React, Vue, Angular
- `backend` - APIs, databases, servers
- `sre` - Infrastructure, monitoring, on-call
- `qa` - Testing, automation, quality

### Create Project-Type Profiles

- `microservice` - Docker, K8s, service mesh
- `monorepo` - Multiple projects, shared deps
- `open-source` - Public repos, community
- `enterprise` - VPN, compliance, audit

### Create Context Profiles

- `morning` - Daily standup, planning
- `deep-work` - Focus mode, minimal distractions
- `debugging` - Logging, tracing, profiling
- `learning` - Documentation, tutorials, examples

## Need Help?

See the main README: [../README.md](../README.md)

Or run:
```bash
ai --help
ai profile --help
ai mcp --help
```
