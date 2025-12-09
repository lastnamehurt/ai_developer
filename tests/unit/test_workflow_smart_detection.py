"""Tests for workflow smart issue detection."""
import pytest
from aidev.workflow import detect_issue_context


def test_detect_jira_key():
    """Detect Jira issue keys (ABC-123 pattern)."""
    result = detect_issue_context("ABC-123")
    assert result["is_issue"] is True
    assert result["issue_type"] == "jira"
    assert result["issue_id"] == "ABC-123"
    assert result["detected_pattern"] == "jira_key"


def test_detect_jira_key_in_text():
    """Detect Jira key embedded in longer text."""
    result = detect_issue_context("Please review PROJ-456 for context")
    assert result["is_issue"] is True
    assert result["issue_type"] == "jira"
    assert result["issue_id"] == "PROJ-456"


def test_detect_jira_url():
    """Detect Atlassian Jira URLs."""
    result = detect_issue_context("https://mycompany.atlassian.net/browse/ISSUE-789")
    assert result["is_issue"] is True
    assert result["issue_type"] == "jira"
    assert result["detected_pattern"] == "atlassian_url"


def test_detect_github_url():
    """Detect GitHub issue URLs."""
    result = detect_issue_context("https://github.com/owner/repo/issues/42")
    assert result["is_issue"] is True
    assert result["issue_type"] == "github"
    assert result["issue_id"] == "owner/repo#42"
    assert result["detected_pattern"] == "github_url"


def test_detect_github_shorthand():
    """Detect GitHub shorthand notation (owner/repo#123)."""
    result = detect_issue_context("owner/repo#99")
    assert result["is_issue"] is True
    assert result["issue_type"] == "github"
    assert result["issue_id"] == "owner/repo#99"
    assert result["detected_pattern"] == "github_shorthand"


def test_detect_no_issue_plain_text():
    """Return False for plain text without issue patterns."""
    result = detect_issue_context("This is just plain text without any issues")
    assert result["is_issue"] is False
    assert result["issue_type"] is None
    assert result["issue_id"] is None


def test_detect_no_issue_empty():
    """Handle None and empty string gracefully."""
    assert detect_issue_context(None)["is_issue"] is False
    assert detect_issue_context("")["is_issue"] is False
    assert detect_issue_context("   ")["is_issue"] is False


def test_detect_priority_jira_over_github():
    """If both patterns present, Jira takes precedence (order of checks)."""
    text = "Fix ABC-123 see https://github.com/org/repo/issues/1"
    result = detect_issue_context(text)
    # Jira pattern checked first in implementation
    assert result["issue_type"] == "jira"
    assert result["issue_id"] == "ABC-123"


def test_detect_edge_case_lowercase_jira():
    """Lowercase Jira keys should NOT match (must be uppercase)."""
    result = detect_issue_context("abc-123")
    assert result["is_issue"] is False


def test_detect_edge_case_partial_github():
    """Incomplete GitHub patterns should not match."""
    assert detect_issue_context("github.com/owner")["is_issue"] is False
    assert detect_issue_context("owner/repo")["is_issue"] is False  # Missing #number


def test_detect_gitlab_url():
    """Detect GitLab issue URLs."""
    result = detect_issue_context("https://gitlab.com/owner/repo/-/issues/42")
    assert result["is_issue"] is True
    assert result["issue_type"] == "gitlab"
    assert result["issue_id"] == "owner/repo!42"
    assert result["detected_pattern"] == "gitlab_url"


def test_detect_gitlab_mr_url():
    """Detect GitLab merge request URLs."""
    result = detect_issue_context("https://gitlab.com/owner/project/-/merge_requests/123")
    assert result["is_issue"] is True
    assert result["issue_type"] == "gitlab"
    assert result["detected_pattern"] == "gitlab_url"


def test_detect_gitlab_self_hosted():
    """Detect self-hosted GitLab instances."""
    result = detect_issue_context("https://gitlab.mycompany.com/team/project/-/issues/99")
    assert result["is_issue"] is True
    assert result["issue_type"] == "gitlab"
    assert result["detected_pattern"] == "gitlab_self_hosted_url"


def test_detect_gitlab_shorthand():
    """Detect GitLab shorthand notation (owner/repo!123)."""
    result = detect_issue_context("owner/repo!456")
    assert result["is_issue"] is True
    assert result["issue_type"] == "gitlab"
    assert result["issue_id"] == "owner/repo!456"
    assert result["detected_pattern"] == "gitlab_shorthand"


def test_detect_github_pr_url():
    """Detect GitHub pull request URLs."""
    result = detect_issue_context("https://github.com/owner/repo/pull/789")
    assert result["is_issue"] is True
    assert result["issue_type"] == "github"
    assert result["issue_id"] == "owner/repo#789"
