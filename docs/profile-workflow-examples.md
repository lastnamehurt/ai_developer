# Profile Workflow Examples

This document shows practical examples of how to use different MCP profiles together to complete engineering tasks efficiently.

## Table of Contents

- [Example 1: Feature Development Workflow](#example-1-feature-development-workflow)
  - [Step 1: Research Phase](#step-1-research-phase-research-profile)
  - [Step 2: Planning & JIRA Creation](#step-2-planning--jira-creation-default-profile)
  - [Step 3: Core Development](#step-3-core-development-memory-profile)
  - [Step 4: Testing & Quality Assurance](#step-4-testing--quality-assurance-qa-profile)
  - [Step 5: Deployment & Operations](#step-5-deployment--operations-devops-profile)
- [Example 2: Bug Investigation & Fix](#example-2-bug-investigation--fix)
  - [Step 1: Information Gathering](#step-1-information-gathering-research--devops)
  - [Step 2: Root Cause Analysis](#step-2-root-cause-analysis-memory)
  - [Step 3: Fix & Testing](#step-3-fix--testing-default--qa)
  - [Step 4: Deployment](#step-4-deployment-devops)
- [Example 3: Code Review & Knowledge Sharing](#example-3-code-review--knowledge-sharing)
  - [Step 1: Review Preparation](#step-1-review-preparation-memory)
  - [Step 2: Deep Code Review](#step-2-deep-code-review-devops)
  - [Step 3: Testing Validation](#step-3-testing-validation-qa)
  - [Step 4: Documentation](#step-4-documentation-research)
- [Profile Selection Guidelines](#profile-selection-guidelines)
- [Best Practices](#best-practices)
- [Environment Requirements](#environment-requirements)
- [Profile Switching](#profile-switching)

## Example 1: Feature Development Workflow

**Task**: Implement user authentication feature from research to deployment

### Step 1: Research Phase (`research` profile)
```bash
# Start with research profile for information gathering
ai claude --profile research

# Ask Claude:
# "Research modern authentication patterns for Node.js applications"
# "Find examples of JWT implementation with refresh tokens"
# "What are the security best practices for password hashing?"
```

**Why research profile?**
- DuckDuckGo search for latest patterns
- Compass for navigation through documentation
- Sequential thinking for structured research

### Step 2: Planning & JIRA Creation (`default` profile)
```bash
# Switch to default for basic development + JIRA
ai cursor --profile default

# Ask Claude:
# "Create a JIRA ticket for implementing JWT authentication"
# "Break down the authentication feature into subtasks"
# "Help me plan the database schema for users and sessions"
```

**Why default profile?**
- Atlassian integration for JIRA ticket creation
- Git operations for branch planning
- Filesystem access for project exploration

### Step 3: Core Development (`memory` profile)
```bash
# Use memory for enhanced development with memory
ai claude --profile memory

# Ask Claude:
# "Remember my authentication implementation preferences"
# "Help me implement the JWT middleware based on our earlier research"
# "Store the database schema we designed for future reference"
```

**Why memory profile?**
- Memory servers remember context across sessions
- Filesystem + git for code implementation
- Memory bank stores implementation decisions

### Step 4: Testing & Quality Assurance (`qa` profile)
```bash
# Switch to QA profile for testing
ai cursor --profile qa

# Ask Claude:
# "Generate Cypress tests for the authentication flow"
# "Run the test overlap analyzer to check coverage"
# "Create security test cases for JWT validation"
```

**Why qa profile?**
- Cypress integration for E2E testing
- Test overlap analyzer for coverage analysis
- GitLab read-only for CI/CD pipeline checks

### Step 5: Deployment & Operations (`devops` profile)
```bash
# Use devops for deployment and infrastructure
ai claude --profile devops

# Ask Claude:
# "Update the Kubernetes deployment for the authentication service"
# "Create a GitLab merge request with deployment instructions"
# "Help me configure environment variables for production"
```

**Why devops profile?**
- GitLab write access for MR creation
- Kubernetes integration for deployment configs
- Full repository operations

## Example 2: Bug Investigation & Fix

**Task**: Investigate and fix a production authentication issue

### Step 1: Information Gathering (`research` + `devops`)
```bash
# Start with research for similar issues
ai claude --profile research
# "Search for common JWT expiration issues in Node.js"

# Switch to devops for system investigation
ai cursor --profile devops
# "Check the Kubernetes logs for authentication service"
# "Review recent GitLab deployments that might have caused this"
```

### Step 2: Root Cause Analysis (`memory`)
```bash
# Use memory with memory for detailed analysis
ai claude --profile memory
# "Remember the production issue details I'm sharing"
# "Analyze the authentication code for potential race conditions"
# "Store the root cause analysis for the postmortem"
```

### Step 3: Fix & Testing (`default` + `qa`)
```bash
# Default profile for the fix
ai cursor --profile default
# "Create a JIRA ticket for this production bug"
# "Help me implement the fix for the JWT race condition"

# QA profile for validation
ai claude --profile qa
# "Create regression tests for this specific bug"
# "Verify the fix doesn't break existing authentication tests"
```

### Step 4: Deployment (`devops`)
```bash
# Deploy the hotfix
ai cursor --profile devops
# "Create an emergency merge request for the hotfix"
# "Update the Kubernetes deployment with the urgent patch"
# "Monitor the deployment through GitLab pipelines"
```

## Example 3: Code Review & Knowledge Sharing

**Task**: Review a team member's pull request and share knowledge

### Step 1: Review Preparation (`memory`)
```bash
# Load context and prepare for review
ai claude --profile memory
# "Remember the coding standards and patterns we established"
# "Load the context about this feature from our previous discussions"
```

### Step 2: Deep Code Review (`devops`)
```bash
# Access the full repository for comprehensive review
ai cursor --profile devops
# "Review this GitLab merge request for security issues"
# "Check if the changes follow our established patterns"
# "Suggest improvements to the Kubernetes configuration"
```

### Step 3: Testing Validation (`qa`)
```bash
# Verify testing completeness
ai claude --profile qa
# "Analyze the test coverage for this merge request"
# "Run the test overlap analyzer on the new tests"
# "Suggest additional edge cases to test"
```

### Step 4: Documentation (`research`)
```bash
# Research and document best practices
ai cursor --profile research
# "Find documentation about this pattern for the team wiki"
# "Research if there are newer approaches to this problem"
# "Help me write a knowledge sharing document"
```

## Profile Selection Guidelines

### When to use each profile:

**`default`** - Daily development work
- Basic coding tasks
- JIRA ticket management  
- Git operations
- General development

**`memory`** - Complex, ongoing projects
- Long-term feature development
- When you need AI to remember context
- Complex architectural decisions
- Cross-session knowledge retention

**`devops`** - Infrastructure & operations
- Deployment and DevOps tasks
- Repository management
- Kubernetes operations
- GitLab administration
- Production troubleshooting

**`qa`** - Testing & quality assurance
- Writing and running tests
- Test coverage analysis
- Quality gates and validation
- CI/CD pipeline testing

**`research`** - Investigation & learning
- Technology research
- Problem investigation
- Learning new patterns
- Information gathering
- External documentation search

## Best Practices

1. **Start Light**: Begin with `default` or `research`, upgrade to specialized profiles as needed
2. **Context Switching**: Use `memory` when you need AI to remember across multiple sessions
3. **Security**: Use `qa` profile for security-sensitive reviews (read-only GitLab access)
4. **Operations**: Switch to `devops` only when you need write access to infrastructure
5. **Memory Management**: Use `memory` to store important decisions and context for team continuity

## Environment Requirements

Make sure your `~/.local/ai-dev/.env` has the required variables:

```bash
# Required for devops and qa profiles
GITLAB_PERSONAL_ACCESS_TOKEN=your-gitlab-token
GITLAB_API_URL=https://gitlab.example.com/api/v4

# Optional but recommended
KUBECONFIG=/path/to/your/kubeconfig
MEMORY_BANK_ROOT=~/.local/ai-dev/memory-banks
```

## Profile Switching

You can switch profiles mid-task by starting a new session:
```bash
ai claude --profile research    # Research the problem
# <work with Claude>
# Exit Claude

ai cursor --profile devops    # Switch to operations
# <work with Cursor>
```

Each profile provides a different lens and toolset for approaching the same problem.