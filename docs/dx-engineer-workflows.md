# Developer Experience Engineer Workflows

This document describes workflows specifically designed for Developer Experience (DX) Engineers. These workflows help automate common DX tasks like creating onboarding guides, improving error messages, analyzing developer feedback, and creating migration guides.

## Overview

DX Engineers focus on improving the developer experience across:
- **Onboarding**: Getting new developers productive quickly
- **Documentation**: Clear, actionable guides and references
- **Error Messages**: Helpful, actionable feedback
- **Migration Guides**: Smooth transitions between versions
- **Developer Feedback**: Understanding pain points and priorities
- **CI/CD Experience**: Faster feedback loops and clearer errors
- **Troubleshooting**: Self-service guides for common issues

## Available Workflows

### 1. `onboarding_guide`

**Purpose**: Create comprehensive onboarding guides for new developers.

**When to use**:
- New team members joining
- Creating "Getting Started" documentation
- Updating onboarding materials
- Documenting project setup procedures

**Usage**:
```bash
# From a ticket describing onboarding needs
ai workflow onboarding_guide --ticket "PROJ-123"

# From existing documentation to improve
ai workflow onboarding_guide docs/README.md

# From a project path to analyze
ai workflow onboarding_guide "Describe onboarding needs for this project"
```

**Workflow Steps**:
1. **understand_requirements**: Analyzes ticket or input to understand onboarding needs
2. **analyze_existing_docs**: Reviews existing documentation for gaps
3. **plan_onboarding_structure**: Creates outline for onboarding guide
4. **draft_onboarding_guide**: Generates comprehensive onboarding documentation

**Example Input**:
- Ticket: "Create onboarding guide for new backend engineers"
- File: Existing README.md or setup docs
- Text: "New developers need to understand: database setup, API keys, testing, deployment"

---

### 2. `error_message_improver`

**Purpose**: Analyze and improve error messages and developer-facing feedback.

**When to use**:
- Error messages are unclear or unhelpful
- Developers frequently ask about error meanings
- Want to make errors more actionable
- Improving developer feedback loops

**Usage**:
```bash
# Analyze error messages from a file
ai workflow error_message_improver error_messages.txt

# From a ticket about error message improvements
ai workflow error_message_improver --ticket "DX-456"
```

**Workflow Steps**:
1. **analyze_error_messages**: Identifies clarity and actionability issues
2. **plan_improvements**: Designs better error message structure
3. **draft_improved_messages**: Creates improved error messages with context

**Example Input**:
```
Error: Connection failed
Error: Invalid input
Error: Permission denied
```

**Output**: Improved messages with:
- Clear context about what failed
- Actionable next steps
- Links to relevant documentation
- Examples of correct usage

---

### 3. `migration_guide`

**Purpose**: Create migration guides for breaking changes, API updates, or major version upgrades.

**When to use**:
- Major version releases with breaking changes
- API deprecations
- Database schema migrations
- Framework upgrades
- Configuration changes

**Usage**:
```bash
# From a ticket describing migration needs
ai workflow migration_guide --ticket "REL-2.0"

# From a changelog or diff
ai workflow migration_guide CHANGELOG.md

# From a GitHub PR with breaking changes
ai workflow migration_guide --ticket "owner/repo#123"
```

**Workflow Steps**:
1. **understand_changes**: Parses changelog, diff, or ticket to understand changes
2. **assess_impact**: Identifies affected areas and breaking changes
3. **plan_migration_steps**: Creates step-by-step migration plan
4. **draft_migration_guide**: Generates comprehensive migration documentation

**Example Output Structure**:
- Overview of changes
- Before/after code examples
- Step-by-step migration instructions
- Common pitfalls and solutions
- Rollback procedures

---

### 4. `api_doc_improver`

**Purpose**: Improve API documentation by analyzing code, existing docs, and developer feedback.

**When to use**:
- API documentation is incomplete or unclear
- Developers struggle to use APIs
- Adding examples or use cases
- Updating docs after API changes

**Usage**:
```bash
# Improve API docs from existing documentation
ai workflow api_doc_improver docs/api.md

# From a ticket about API documentation
ai workflow api_doc_improver --ticket "DOC-789"

# Analyze API code and improve docs
ai workflow api_doc_improver "Review and improve API documentation for src/api/"
```

**Workflow Steps**:
1. **analyze_api_docs**: Reviews existing API documentation for gaps
2. **assess_api_code**: Analyzes actual API implementation for discrepancies
3. **plan_doc_improvements**: Identifies missing examples, unclear descriptions
4. **draft_improved_docs**: Creates improved documentation with examples

**Improvements Typically Include**:
- Clear parameter descriptions
- Request/response examples
- Error handling documentation
- Authentication examples
- Rate limiting information
- Code samples in multiple languages

---

### 5. `developer_feedback_analyzer`

**Purpose**: Analyze developer feedback, surveys, or support tickets to identify common pain points and improvement opportunities.

**When to use**:
- After developer surveys
- Analyzing support ticket patterns
- Understanding developer frustrations
- Prioritizing DX improvements

**Usage**:
```bash
# From a ticket with developer feedback
ai workflow developer_feedback_analyzer --ticket "FEEDBACK-2024"

# From a file with survey responses
ai workflow developer_feedback_analyzer survey_responses.txt

# From multiple support tickets
ai workflow developer_feedback_analyzer support_tickets.csv
```

**Workflow Steps**:
1. **parse_feedback**: Extracts themes and patterns from feedback
2. **identify_patterns**: Groups similar issues and identifies trends
3. **prioritize_improvements**: Ranks improvements by impact and effort
4. **draft_improvement_plan**: Creates actionable improvement roadmap

**Output Includes**:
- Common pain points ranked by frequency
- Suggested improvements with priority
- Quick wins vs. long-term improvements
- Impact assessment

---

### 6. `troubleshooting_guide`

**Purpose**: Create troubleshooting guides from bug reports, error logs, or support tickets.

**When to use**:
- Common issues keep appearing in support
- Creating self-service documentation
- Documenting known issues and workarounds
- Reducing support burden

**Usage**:
```bash
# From a bug ticket
ai workflow troubleshooting_guide --ticket "BUG-123"

# From error logs
ai workflow troubleshooting_guide error_logs.txt

# From multiple support tickets
ai workflow troubleshooting_guide "Common issues: connection errors, auth failures, timeout issues"
```

**Workflow Steps**:
1. **parse_issues**: Extracts problem descriptions and error messages
2. **categorize_problems**: Groups similar issues together
3. **plan_troubleshooting_steps**: Creates diagnostic flow
4. **draft_troubleshooting_guide**: Generates step-by-step troubleshooting guide

**Output Structure**:
- Problem symptoms
- Diagnostic steps
- Common causes
- Solutions and workarounds
- Prevention tips

---

### 7. `quickstart_creator`

**Purpose**: Create quickstart or getting started guides by analyzing project structure.

**When to use**:
- New project needs quickstart guide
- Existing quickstart is outdated
- Simplifying onboarding for new developers
- Creating "Hello World" examples

**Usage**:
```bash
# Analyze project and create quickstart
ai workflow quickstart_creator "Create a quickstart guide for this project"

# From existing documentation
ai workflow quickstart_creator docs/README.md

# From a ticket
ai workflow quickstart_creator --ticket "QUICKSTART-1"
```

**Workflow Steps**:
1. **understand_project_structure**: Analyzes project to understand setup requirements
2. **identify_setup_requirements**: Lists dependencies, configuration, and prerequisites
3. **plan_quickstart_steps**: Creates minimal viable setup path
4. **draft_quickstart_guide**: Generates step-by-step quickstart guide

**Output Includes**:
- Prerequisites checklist
- Installation steps
- Configuration setup
- "Hello World" example
- Next steps and resources

---

### 8. `ci_cd_dx_improver`

**Purpose**: Improve CI/CD developer experience by analyzing pipeline failures and developer feedback.

**When to use**:
- CI/CD errors are unclear
- Build times are too slow
- Developers struggle with pipeline failures
- Want faster feedback loops
- Improving test failure messages

**Usage**:
```bash
# From CI/CD failure logs
ai workflow ci_cd_dx_improver ci_failures.log

# From a ticket about CI/CD improvements
ai workflow ci_cd_dx_improver --ticket "CI-456"

# Analyze developer feedback about CI/CD
ai workflow ci_cd_dx_improver "Developers report: slow builds, unclear errors, hard to debug"
```

**Workflow Steps**:
1. **analyze_ci_issues**: Parses CI/CD failures and error patterns
2. **assess_developer_impact**: Identifies developer pain points
3. **plan_dx_improvements**: Designs better error messages and faster feedback
4. **draft_improvement_proposal**: Creates improvement plan with priorities

**Typical Improvements**:
- Clearer error messages in CI output
- Faster feedback loops (parallelization, caching)
- Better test failure diagnostics
- Improved local development experience
- Pre-commit hooks and validation

---

## Workflow Execution Modes

All workflows support multiple execution modes:

### Interactive Handoff (Default)
```bash
ai workflow onboarding_guide README.md
```
Creates a manifest and hands off to your assistant for interactive execution.

### Automated Execution
```bash
ai workflow onboarding_guide README.md --execute
```
Runs all steps automatically without interaction.

### Resume from Step
```bash
ai workflow onboarding_guide README.md --from-step "plan_onboarding_structure"
```
Resumes execution from a specific step.

### Single Step
```bash
ai workflow onboarding_guide README.md --step-only
```
Runs only the first step.

## Best Practices

### 1. **Iterative Refinement**
Start with a workflow run, review the output, then refine:
```bash
# Initial run
ai workflow onboarding_guide --ticket "ONBOARD-1"

# Review output, then refine specific sections
ai workflow onboarding_guide --from-step "draft_onboarding_guide" --ticket "ONBOARD-1"
```

### 2. **Combine Workflows**
Chain workflows for comprehensive documentation:
```bash
# Create quickstart
ai workflow quickstart_creator "New project setup"

# Then improve it
ai workflow doc_improver .aidev/workflow-runs/quickstart_creator-*.proposal.md
```

### 3. **Use Memory Bank**
The memory-bank MCP helps workflows remember context:
- Project-specific preferences
- Common patterns
- Previous improvements
- Developer feedback history

### 4. **Profile Selection**
Workflows automatically use appropriate profiles:
- `onboarding` - For understanding and exploration
- `documentation-writer` - For documentation tasks
- `code-surgeon` - For analysis and impact assessment
- `pair-programmer` - For planning and implementation
- `devops` - For CI/CD related tasks

## Customization

### Adding Custom Steps

You can extend workflows by editing `.aidev/workflows.yaml`:

```yaml
onboarding_guide:
  description: "Create comprehensive onboarding guide"
  steps:
    - name: understand_requirements
      profile: onboarding
      prompt: ticket_understander
    # Add your custom step here
    - name: validate_with_team
      profile: pair-programmer
      prompt: custom_validation_prompt
```

### Creating Custom Prompts

Add new prompts to `src/aidev/prompts/`:
```bash
# Create a new prompt file
echo "You are a DX Engineer. Analyze developer feedback and identify..." > \
  src/aidev/prompts/feedback_analyzer.txt
```

Then reference it in your workflow:
```yaml
- name: analyze_feedback
  profile: documentation-writer
  prompt: feedback_analyzer
```

## Examples

### Example 1: Complete Onboarding Package
```bash
# 1. Create quickstart
ai workflow quickstart_creator "Create quickstart for new developers"

# 2. Create full onboarding guide
ai workflow onboarding_guide --ticket "ONBOARD-2024"

# 3. Create troubleshooting guide for common setup issues
ai workflow troubleshooting_guide "Common setup issues: npm install fails, database connection errors"
```

### Example 2: API Documentation Improvement
```bash
# 1. Analyze existing API docs
ai workflow api_doc_improver docs/api.md

# 2. Improve error messages
ai workflow error_message_improver "API error messages need improvement"

# 3. Create migration guide for API v2
ai workflow migration_guide --ticket "API-V2-MIGRATION"
```

### Example 3: Developer Feedback Loop
```bash
# 1. Analyze developer feedback
ai workflow developer_feedback_analyzer --ticket "Q4-DEVELOPER-SURVEY"

# 2. Create improvement plan
ai workflow ci_cd_dx_improver "Based on feedback, improve CI/CD experience"

# 3. Document improvements
ai workflow doc_improver improvement_plan.md
```

## Troubleshooting

### Workflow Not Found
```bash
# Ensure workflows.yaml exists
ls .aidev/workflows.yaml

# List available workflows
ai workflow list
```

### Prompt Not Found
```bash
# Check available prompts
ls src/aidev/prompts/

# Ensure prompt file matches workflow definition
```

### Profile Not Found
```bash
# List available profiles
ai profile list

# Check profile exists in your project
ai profile show documentation-writer
```

## Related Documentation

- [Workflow System Overview](workflows.md) - General workflow documentation
- [Profiles Catalog](profiles.md) - Available profiles for different tasks
- [CLAUDE.md](../CLAUDE.md) - Project architecture and development guide
