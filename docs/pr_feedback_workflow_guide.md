# Address PR/MR Feedback Workflow Guide

## Overview

The **Address PR/MR Feedback** workflow automates the process of comprehensively addressing code review feedback from both GitHub Pull Requests and GitLab Merge Requests. Instead of manually tracking multiple comments and making isolated changes, this workflow orchestrates a structured approach to analyzing feedback, planning responses, implementing changes, and preparing for re-review.

**Problem it solves:** Code reviews often contain multiple types of feedback (questions, suggestions, required changes, style issues). Developers end up juggling comments across different platforms, implementing changes in isolation, and sometimes missing feedback categories or failing to verify that all concerns were addressed.

**Solution:** This workflow uses Claude Code as a workflow executor to guide you through each phase systematically, using the `WorkflowManifest` helper to track progress incrementally.

---

## Quick Start

### For GitHub Pull Requests

```bash
# Provide your PR URL or number
ai workflow address_pr_feedback "https://github.com/owner/repo/pull/123"
# or
ai workflow address_pr_feedback "owner/repo#123"
```

### For GitLab Merge Requests

```bash
# Provide your MR URL or IID
ai workflow address_pr_feedback "https://gitlab.com/group/project/-/merge_requests/456"
# or
ai workflow address_pr_feedback "group/project!456"
```

### Or Use Interactive Mode

If Claude Code launches interactively, you'll be guided through each step with clear prompts.

---

## Workflow Steps

### Step 1: Fetch & Categorize Feedback

**What happens:** Claude Code fetches all review comments from the PR/MR and categorizes them into:
- **Required Changes**: Must-fix issues (bugs, security, breaking changes)
- **Strong Suggestions**: Improvements recommended by maintainers
- **Questions/Clarifications**: Places where code intent is unclear
- **Style/Nitpicks**: Minor formatting or naming preferences
- **Positive feedback**: Comments acknowledging good parts (for context)

**What you need to do:**
- Provide the PR/MR URL or identifier
- Claude Code will read all comments and extract feedback

**Example output:**
```
REQUIRED CHANGES:
1. The error handling in authenticate() will crash on network timeout
2. SQL injection vulnerability in the query builder
3. Missing test for the new admin panel feature

STRONG SUGGESTIONS:
1. Consider using async/await instead of callbacks
2. Function naming could be clearer (get_data → fetch_user_data)

QUESTIONS:
1. Why was the legacy API endpoint not deprecated?
2. What's the expected timeout for the cache?

STYLE:
1. Inconsistent indentation in utils.py
2. Missing docstrings on public methods
```

---

### Step 2: Plan Response Strategy

**What happens:** Claude Code creates a prioritized plan for addressing the feedback:
1. Groups related changes
2. Identifies dependencies (some changes may need to happen first)
3. Flags potential conflicts or breaking changes
4. Estimates impact on tests and documentation

**What you need to do:**
- Review the plan and provide any additional context
- Flag if you disagree with priorities or if certain changes are impossible
- Clarify any ambiguous feedback

**Example plan:**
```
IMPLEMENTATION PLAN:

PHASE 1: CRITICAL FIXES (blocking re-review)
├─ Fix error handling in authenticate() - sync (1 function)
├─ Add SQL injection protection - moderate (3 functions)
└─ Add admin panel tests - moderate (2 test files)

PHASE 2: STRONG IMPROVEMENTS (recommended)
├─ Refactor callbacks to async/await - 4 functions affected
└─ Rename and reorganize utility functions - low risk

PHASE 3: STYLE & DOCUMENTATION
├─ Fix indentation in utils.py
├─ Add docstrings to public methods
└─ Update CHANGELOG with deprecation notice

DEPENDENCIES:
- Phase 1 must complete before requesting re-review
- Phase 2 can run in parallel with Phase 1 (no conflicts)
- Phase 3 can run anytime after Phase 1

RISK ASSESSMENT:
- Cache timeout change requires coordination with deployment team
- Async refactor may break compatibility with legacy code paths
```

---

### Step 3: Implement Changes

**What happens:** Claude Code generates code changes based on the plan:
1. Creates or modifies files as needed
2. Ensures changes address the specific feedback points
3. Maintains consistency with existing code patterns
4. Adds necessary tests or documentation

**What you need to do:**
- Review each change before it's committed
- Request modifications if something doesn't match your intent
- Test changes locally if they're complex

**Example interaction:**
```
Claude: I'm implementing the SQL injection fix in query_builder.py.
        This uses parameterized queries instead of string concatenation.
        Should I also add type hints to the function signature?

You: Yes, please use the existing type hint pattern from other functions.

Claude: ✓ Changes implemented with type hints added.
        Files modified: query_builder.py, tests/test_query_builder.py
        Ready to verify these changes? (y/n)
```

---

### Step 4: Verify Feedback Addressed

**What happens:** Claude Code systematically checks that all feedback has been addressed:
1. Maps each original comment to specific changes made
2. Verifies tests pass and cover new functionality
3. Checks for any missed or partially-addressed comments
4. Confirms no new issues were introduced

**What you need to do:**
- Run tests locally (Claude will provide the commands)
- Manually spot-check critical changes
- Confirm nothing was missed

**Example verification:**
```
VERIFICATION CHECKLIST:

✓ Required Change #1 (error handling crash)
  → Fixed in authenticate() with try/except for network timeout
  → Test added: test_authenticate_network_timeout()

✓ Required Change #2 (SQL injection)
  → Parameterized queries implemented in query_builder.py
  → Tests added: test_sql_injection_prevention()

✓ Required Change #3 (admin panel tests)
  → New tests added in tests/test_admin_panel.py
  → Coverage: 8 test cases

⚠ Strong Suggestion #1 (async/await)
  → Noted for follow-up work (out of scope for this review cycle)
  → Added TODO comment in code with reference to original feedback

⚠ Strong Suggestion #2 (naming)
  → Applied to primary functions
  → Some internal helpers kept for backward compatibility

✓ All style issues resolved
✓ All tests passing (42 total, 6 new)
✓ No linting errors
```

---

### Step 5: Draft Response Comments

**What happens:** Claude Code drafts professional response comments for each feedback item:
1. Acknowledges the concern
2. Explains how it was addressed
3. Links to specific commits or files
4. Asks clarifying questions if needed
5. Thanks reviewers for feedback

**What you need to do:**
- Review draft comments
- Edit as needed to match your tone/style
- Confirm they're ready to post

**Example comments:**
```
Regarding SQL injection vulnerability:
Great catch! I've refactored the query_builder to use parameterized
queries throughout. This eliminates the risk of injection attacks.
See commit abc1234 for the implementation and new test coverage.

Regarding error handling crash:
You're right—I added proper exception handling for network timeouts
in authenticate(). The function now returns a clear error message
instead of crashing. Tests in test_authenticate_network_timeout()
verify this behavior.

Regarding async/await suggestion:
This is a great suggestion for improving performance. Rather than
refactor everything in this PR, I've added a TODO comment to track
this as future work. The current implementation is stable and tested.
```

---

### Step 6: Prepare for Review

**What happens:** Claude Code prepares everything for re-review:
1. Commits all changes with clear messages
2. Generates a summary of changes made
3. Creates or updates the PR/MR description
4. Provides recommendations for re-review focus areas

**What you need to do:**
- Review the commit history
- Confirm the PR/MR description is accurate
- Push changes and request re-review

**Example summary:**
```
CHANGES SUMMARY:

Files Modified: 7
Files Added: 3
Commits: 4

COMMITS:
1. fix(auth): add error handling for network timeouts
   - Prevents crash when timeout occurs
   - Test coverage: test_authenticate_network_timeout

2. fix(db): prevent SQL injection in query builder
   - Uses parameterized queries
   - Test coverage: test_sql_injection_prevention

3. test(admin): add comprehensive admin panel tests
   - 8 new test cases
   - Coverage: 95% of admin code

4. style: fix indentation and add docstrings
   - utils.py: fixed inconsistent indentation
   - Added docstrings to 12 public methods

PULL REQUEST DESCRIPTION UPDATED:
- Addressed all required changes
- Acknowledged strong suggestions
- Listed verification tests
- Provided implementation summary
```

---

## Supported Platforms

### GitHub
- ✅ Public repositories
- ✅ Private repositories (with proper auth)
- ✅ GitHub Enterprise
- Requires: `GITHUB_TOKEN` or `GITHUB_PERSONAL_ACCESS_TOKEN`

### GitLab
- ✅ Public projects
- ✅ Private projects (with proper auth)
- ✅ GitLab.com and self-hosted instances
- Requires: `GITLAB_PERSONAL_ACCESS_TOKEN`

---

## How It Uses WorkflowManifest

Each step of the workflow is tracked in a manifest JSON file:

```json
{
  "workflow": "address_pr_feedback",
  "pr_url": "https://github.com/owner/repo/pull/123",
  "steps": [
    {
      "name": "fetch_and_categorize_feedback",
      "output": {
        "status": "ok",
        "result": "Fetched 12 comments: 3 required changes, 4 suggestions, 2 questions, 3 style"
      }
    },
    {
      "name": "plan_response_strategy",
      "output": {
        "status": "ok",
        "result": "Created implementation plan with 3 phases and no blocking dependencies"
      }
    },
    {
      "name": "implement_changes",
      "output": {
        "status": "ok",
        "result": "7 files modified, 3 files added, all tests passing"
      }
    }
    // ... more steps
  ]
}
```

**Key advantage:** You can stop at any step and resume later. The manifest tracks exactly where you left off, so re-running the workflow picks up from the last completed step.

---

## Common Patterns & Tips

### Pattern 1: Incremental Feedback Sessions

If you receive feedback in multiple rounds:

```bash
# First round of feedback
ai workflow address_pr_feedback "owner/repo#123"

# Later, more feedback arrives...
# Re-run the workflow (it resumes from where you left off)
ai workflow address_pr_feedback "owner/repo#123"
```

The workflow will fetch new comments and add them to the plan.

### Pattern 2: Skipping Non-Required Changes

If you want to address only "required changes" and leave suggestions for later:

During Step 2 (Plan Response Strategy), tell Claude Code:
```
"I want to address only the required changes in this round.
Can you create a minimal implementation plan that skips suggestions?"
```

### Pattern 3: Custom Feedback Categories

If your team uses specific comment markers:

```
// reviewer: @alice
// type: question
// priority: high

Why was this library chosen over X?
```

Claude Code can detect and prioritize these custom markers during feedback analysis.

### Pattern 4: Coordination with Teammates

If multiple people are responding to feedback:

```bash
# Claude Code detects which comments you've already addressed
# and focuses on remaining ones
ai workflow address_pr_feedback "owner/repo#123" \
  --addressed-by "your-username"
```

---

## Best Practices

### ✅ DO

- **Address all required changes first** - Get these done before suggestions
- **Acknowledge reviewer feedback explicitly** - Thank them and show you understood
- **Add tests for your changes** - Verify the feedback concern is actually fixed
- **Commit clearly** - Use messages that reference the feedback
- **Document decisions** - If you diverge from feedback, explain why
- **Request re-review promptly** - Don't let PRs sit idle

### ❌ DON'T

- **Ignore style feedback entirely** - It matters for consistency
- **Batch changes without tracking** - Use the manifest to stay organized
- **Change scope significantly** - Stick to addressing the feedback
- **Merge without addressing required changes** - Always get them done first
- **Delete feedback comments** - Keep the conversation for history
- **Forget to test** - Always verify your fixes work

---

## Example: Complete Workflow

### Scenario
You created a PR for a new user authentication feature. Reviewers left feedback, and now you're addressing it.

### Execution

```bash
$ ai workflow address_pr_feedback "owner/app#456"

Claude: I'm fetching feedback from your PR...

[Step 1: Fetch & Categorize Feedback]
✓ Found 8 comments from 2 reviewers

REQUIRED CHANGES:
- Error handling missing in password reset flow
- SQL injection vulnerability in user lookup
- No unit tests for new feature

SUGGESTIONS:
- Consider caching user lookups
- Rename authenticate() to validate_credentials()

QUESTIONS:
- What's the expected timeout for password reset email?

STYLE:
- Missing docstrings on 3 public methods

Is this categorization correct? Should I adjust any priorities? (y/n)
```

You review and confirm the categorization:

```
You: This looks good, but the password reset timeout is 5 minutes.
     Please add that context to the implementation plan.
```

Claude continues:

```
[Step 2: Plan Response Strategy]
✓ Created implementation plan

IMPLEMENTATION PLAN:
Phase 1: Required Changes (2 hours estimated)
├─ Add error handling to password reset
├─ Fix SQL injection in user lookup
└─ Add unit tests for new feature

Phase 2: Suggestions (1 hour estimated)
├─ Add user lookup caching
└─ Rename authenticate() (with deprecation path)

Phase 3: Documentation (30 min estimated)
└─ Add docstrings and update README

Ready to proceed with Phase 1? (y/n)
```

You confirm:

```
You: Yes, proceed with Phase 1. I'll review changes as you make them.
```

Claude implements:

```
[Step 3: Implement Changes]
✓ Implementing error handling...
  Files: src/auth.py, tests/test_auth.py

✓ Implementing SQL injection fix...
  Files: src/db.py, tests/test_db.py

✓ Adding unit tests...
  Files: tests/test_auth_new_feature.py

All tests passing (48 total, 6 new). Ready for verification? (y/n)
```

You verify locally and confirm:

```
You: Tests look good. Running my own test suite... All passing!
```

Claude verifies and prepares response:

```
[Step 4: Verify Feedback Addressed]
✓ All required changes addressed and tested

[Step 5: Draft Response Comments]
Here are my draft responses to each comment:

---
Re: "Missing error handling in password reset"
> I've added comprehensive error handling to prevent crashes
> when the email service is down or invalid addresses are used.
> See commit x1y2z3 for details.
---

Re: "SQL injection vulnerability"
> Excellent catch! I've refactored the query to use parameterized
> statements. All queries now use prepared statements. New tests
> verify this prevention.
---

[Ready to push and request re-review]

Summary:
- 3 files modified (auth.py, db.py, tests/)
- 2 files added (new test files)
- 6 new commits
- All feedback addressed

Ready to push? (y/n)
```

```
You: Yes, push and request re-review from @alice and @bob.
```

```
✓ Changes pushed to origin/fix-auth-feedback
✓ PR updated with completion summary
✓ Re-review requested from @alice and @bob

Workflow complete! 🎉
```

---

## Troubleshooting

### Issue: "PR/MR not found"

**Solution:** Verify the URL format:
- GitHub: `owner/repo#123` or full GitHub URL
- GitLab: `group/project!456` or full GitLab URL
- Check that your auth token is set correctly

### Issue: "Missing authentication"

**Solution:** Set required environment variables:
```bash
# GitHub
export GITHUB_TOKEN="ghp_..."

# GitLab
export GITLAB_PERSONAL_ACCESS_TOKEN="glpat-..."
```

### Issue: "Can't connect to repository"

**Solution:** Verify your network and credentials:
```bash
ai doctor  # Runs health checks
```

### Issue: "Workflow stopped mid-step"

**Solution:** The manifest tracks your progress. Re-run the command:
```bash
ai workflow address_pr_feedback "owner/repo#123"
```

It will resume from where it left off.

---

## Integration with Engineering Workflow

This workflow fits into your engineering process like this:

1. **Create feature branch and PR** (see engineering-workflow.md)
2. **Receive code review feedback**
3. **Run address_pr_feedback workflow** ← You are here
4. **Push changes and request re-review**
5. **Merge when approved**

---

## Advanced Usage

### Custom Feedback Processors

If your team uses specialized comment formats, you can extend the workflow:

```bash
ai workflow address_pr_feedback "owner/repo#123" \
  --feedback-markers "reviewer:,priority:,type:" \
  --custom-categories "architecture,performance,security"
```

### Dry Run Mode

Test the workflow without making changes:

```bash
ai workflow address_pr_feedback "owner/repo#123" --dry-run
```

This shows you what would happen without actually modifying files.

### Batch Processing Multiple PRs

Address feedback on multiple PRs:

```bash
ai workflow address_pr_feedback \
  "owner/repo#123" \
  "owner/repo#124" \
  "owner/repo#125"
```

---

## Questions?

See the full workflow manifest guide for implementation details:
- `docs/workflow_manifest_guide.md`

See the engineering workflow for broader context:
- `.aidev/engineering-workflow.md`

---

## Benefits

1. **Systematic**: Every feedback point is tracked and addressed
2. **Transparent**: Clear communication with reviewers about what changed
3. **Testable**: Changes are verified before re-requesting review
4. **Incremental**: You can make progress in phases
5. **Resumable**: Pick up where you left off if interrupted
6. **Collaborative**: Works well with your existing code review process
