# Engineering Task Workflow

This document outlines the standard workflow for completing engineering tasks using Claude Code and other AI assistants.

## Overview

The engineering task workflow consists of two main phases:
1. **Problem Analysis & Planning** - Research the problem and create a JIRA ticket
2. **Implementation & Delivery** - Complete the task, create merge request, and update JIRA status

---

## Phase 1: Problem Analysis & Planning

### Given a Problem, Write a JIRA

1. **Research the problem context**
   - Review related existing JIRA tickets (if referenced)
   - Understand the technical requirements
   - Identify potential impact and related systems

2. **Create JIRA ticket**
   - Use appropriate project (e.g., EDEVE for engineering tasks)
   - Choose appropriate issue type (Task, Bug, Story, etc.)
   - Write clear summary following pattern: `[Action] [Component/System] [Brief Description]`
   - Include detailed description with:
     - Context/Background
     - Specific changes required
     - Expected impact
     - Files to be modified
     - Related issues/tickets

3. **Plan the implementation**
   - Use TodoWrite tool to break down the task into actionable items
   - Identify files that need to be modified
   - Consider testing requirements

---

## Phase 2: Implementation & Delivery

### Given a JIRA, Complete the Task

#### Step 1: Update JIRA Status
- Transition JIRA ticket to **"In Progress"** when starting work

#### Step 2: Create Feature Branch
- Create branch using pattern: `JIRA-###-descriptive-name`
- Example: `EDEVE-417-increase-puma-worker-timeout`

#### Step 3: Implement Changes
- Make necessary code changes
- Follow existing code conventions and patterns
- Ensure changes align with JIRA requirements

#### Step 4: Commit Changes
- **Stage relevant files ONLY** - Never use `git add .` or `git add -A`
- Always specify exact file paths to avoid staging unintended changes
- Write clear commit messages using Conventional Commits format:
  ```
  feat(scope): brief description
  
  - Detailed change 1
  - Detailed change 2
  - Impact/reasoning
  
  JIRA-###
  ```
- Use `--no-verify` flag if needed for pre-commit hooks

#### Step 5: Push Changes
- Push branch with upstream tracking: `git push -u origin branch-name`
- Force push if commit history needs cleaning: `git push --force`

#### Step 6: Create Merge Request
- Title format: `JIRA-###: Brief description`
- Include comprehensive description with:
  - Summary of changes
  - Context/reasoning
  - Test plan checklist
  - Related issues/tickets
- Target appropriate branch (usually `master`)

#### Step 7: Update JIRA Status
- Transition JIRA ticket to **"Code Review"** after creating merge request
- Add merge request link to JIRA comments if needed

#### Step 8: Post-Merge (when applicable)
- After merge request is approved and merged
- Transition JIRA ticket to **"Done"** or **"Complete"**

---

## Tools & Commands

### Essential Git Commands
```bash
# ALWAYS start with fresh default branch and create new branch
git checkout $(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
git pull
git checkout -b JIRA-###-descriptive-name

# Alternative: if you know the default branch name (master/main)
git checkout master  # or main
git pull origin master  # or main

# If working on existing branch, rebase to latest default branch first
git checkout JIRA-###-descriptive-name
git rebase $(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')

# Stage specific files ONLY - NEVER use blanket adds
git add path/to/file
# ❌ NEVER DO: git add . or git add -A (stages everything including unintended files)
# ✅ ALWAYS: specify exact files you modified

# Commit with detailed message
git commit --no-verify "detailed multiline commit message"

# Push with upstream (first time)
git push -u origin branch-name

# Force push after rebase (when needed)
git push --force-with-lease
```

### JIRA Integration
- Use MCP Atlassian tools for JIRA operations
- Always include JIRA ticket number in commit messages
- Link related tickets in JIRA descriptions

### Code Quality
- Run linting and type checking before final push
- Follow existing code patterns and conventions
- Test changes locally when possible if very little setup is required.
---

## Example Workflow

```
Problem: Increase Puma worker timeout to reduce 503 errors

1. Research EPEN-970 (related issue about timeouts)
2. Create EDEVE-417: "Increase Puma worker timeout from 15s to 30s"
3. Transition to "In Progress"
4. Create branch: EDEVE-417-increase-puma-worker-timeout
5. Modify config/puma.rb: worker_timeout 15→30
6. Commit: "feat(config): increase puma worker timeout from 15s to 30s"
7. Push branch
8. Create MR: "EDEVE-417: Increase Puma worker timeout from 15s to 30s"
9. Transition to "Code Review"
10. (After merge) Transition to "Done"
```

---

## Code Review Guidelines

### Staff Engineer Review Principles

As a Staff Engineer, focus reviews on **production readiness** and **critical functionality** rather than over-engineering defensive checks.

#### ✅ **APPROVE** Criteria
- **Functionality works correctly** for the intended use case
- **Clear purpose and value** - solves a real problem effectively
- **Good test coverage** for core functionality
- **Follows existing patterns** and conventions in the codebase
- **Error handling** exists for failure scenarios

#### 🔴 **REQUIRE CHANGES** Only For
- **Code that will crash in production** with likely inputs
- **Silent failures** that would be hard to debug
- **Security vulnerabilities** or data exposure risks
- **Breaking changes** without proper migration strategy
- **Missing critical test coverage** for core functionality

#### 🔶 **SUGGEST** (Not Required)
- **Input validation** for defensive programming (unless crashes are likely)
- **Performance optimizations** for non-critical paths
- **Code style improvements** beyond what linters catch
- **Additional test cases** for edge scenarios
- **Documentation improvements** for maintainability

#### **Review Categories**

**HIGH PRIORITY (Required)**:
- Fix anything that crashes with realistic inputs
- Address silent failures that break core functionality  
- Resolve security issues or data leaks
- Fix breaking changes without migration plans

**MEDIUM PRIORITY (Suggested)**:
- Document decision rationale for future maintainers
- Add performance considerations for high-traffic paths
- Improve error messages for better debugging

**LOW PRIORITY (Nice-to-have)**:
- Defensive input validation for unlikely scenarios
- Additional logging for observability
- Code organization improvements

#### **Review Focus Areas**

1. **Functionality First**: Does it solve the problem correctly?
2. **Production Impact**: What could realistically go wrong?
3. **Testability**: Are the critical paths tested?
4. **Maintainability**: Can future developers understand and modify this?
5. **Performance**: Will this cause issues under load?

#### **Review Anti-Patterns to Avoid**
- ❌ Requiring input validation for every parameter "just in case"
- ❌ Demanding perfect test coverage for trivial edge cases
- ❌ Blocking on code style that linters would catch
- ❌ Over-engineering solutions for simple problems
- ❌ Requiring documentation for self-explanatory code

#### **Sample Review Language**

**For Production-Ready Code**:
> "APPROVE - This successfully centralizes the logging pattern with good test coverage. The error handling is robust and the API is intuitive."

**For Critical Issues**:
> "REQUIRE CHANGES - The `**tags` expansion will crash if a non-hash is passed, which is likely given the calling patterns."

**For Suggestions**:
> "APPROVE with suggestions - Consider adding documentation for the blacklist criteria to help future maintainers understand the filtering logic."

---

## Best Practices

- **Always use TodoWrite** to track progress and break down complex tasks
- **Keep commits focused** - one logical change per commit
- **Stage files intentionally** - Never use `git add .` or `git add -A`, always specify exact file paths
- **Clean commit history** - remove experimental/debugging commits before final push
- **Clear communication** - JIRA descriptions and MR descriptions should be comprehensive
- **Follow conventions** - branch naming, commit messages, code style
- **Update JIRA promptly** - keep status current for team visibility
