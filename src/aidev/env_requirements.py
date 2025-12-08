"""
Environment variable requirements and metadata for MCP servers and tools.

This module tracks which environment variables are required by different
MCP servers and profiles, along with metadata for user-friendly setup.
"""
from __future__ import annotations

from typing import Callable, Optional

from aidev.models import Profile, MCPServerConfig


# Metadata for environment variables: description, where to get it, and whether to encrypt
ENV_VAR_METADATA = {
    "GITHUB_PERSONAL_ACCESS_TOKEN": {
        "description": "GitHub Personal Access Token",
        "short": "GITHUB_TOKEN",
        "url": "https://github.com/settings/tokens",
        "help": "Create a PAT with 'repo' scope",
        "encrypt": True,
        "required_by": ["github"],
    },
    "GITHUB_TOKEN": {
        "description": "GitHub Token (alias for GITHUB_PERSONAL_ACCESS_TOKEN)",
        "short": "GITHUB_TOKEN",
        "url": "https://github.com/settings/tokens",
        "help": "Create a PAT with 'repo' scope",
        "encrypt": True,
        "required_by": ["github"],
    },
    "GITLAB_PERSONAL_ACCESS_TOKEN": {
        "description": "GitLab Personal Access Token",
        "short": "GITLAB_TOKEN",
        "url": "https://gitlab.com/-/user_settings/personal_access_tokens",
        "help": "Create a PAT with 'api' and 'read_user' scopes",
        "encrypt": True,
        "required_by": ["gitlab"],
    },
    "GITLAB_URL": {
        "description": "GitLab instance URL (optional, defaults to https://gitlab.com)",
        "short": "GITLAB_URL",
        "url": None,
        "help": "e.g., https://gitlab.example.com",
        "encrypt": False,
        "required_by": ["gitlab"],
        "optional": True,
    },
    "POSTGRES_URL": {
        "description": "PostgreSQL connection string",
        "short": "POSTGRES_URL",
        "url": "https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-CONNSTRING",
        "help": "e.g., postgresql://user:pass@localhost:5432/dbname",
        "encrypt": True,
        "required_by": ["postgres"],
    },
    "ANTHROPIC_API_KEY": {
        "description": "Anthropic API Key (for Claude tool integration)",
        "short": "ANTHROPIC_API_KEY",
        "url": "https://console.anthropic.com/",
        "help": "Create a key at console.anthropic.com",
        "encrypt": True,
        "required_by": ["claude"],
    },
    "OPENAI_API_KEY": {
        "description": "OpenAI API Key (for GPT models)",
        "short": "OPENAI_API_KEY",
        "url": "https://platform.openai.com/api-keys",
        "help": "Create a key at platform.openai.com",
        "encrypt": True,
        "required_by": [],
    },
    "PLAYWRIGHT_BROWSERS_PATH": {
        "description": "Playwright browsers cache directory",
        "short": "PLAYWRIGHT_BROWSERS_PATH",
        "url": None,
        "help": "Usually ${HOME}/.cache/ms-playwright",
        "encrypt": False,
        "required_by": ["qa"],
        "optional": True,
    },
    "KUBECONFIG": {
        "description": "Kubernetes config file path",
        "short": "KUBECONFIG",
        "url": None,
        "help": "Usually ${HOME}/.kube/config",
        "encrypt": False,
        "required_by": ["k8s"],
        "optional": True,
    },
    "GITLAB_API_URL": {
        "description": "GitLab API URL (optional, defaults to https://gitlab.com/api/v4)",
        "short": "GITLAB_API_URL",
        "url": None,
        "help": "e.g., https://gitlab.example.com/api/v4",
        "encrypt": False,
        "required_by": ["gitlab"],
        "optional": True,
    },
    "GITLAB_READ_ONLY_MODE": {
        "description": "GitLab read-only mode (optional, defaults to false)",
        "short": "GITLAB_READ_ONLY_MODE",
        "url": None,
        "help": "Set to 'true' for read-only access",
        "encrypt": False,
        "required_by": ["gitlab"],
        "optional": True,
    },
    "USE_GITLAB_WIKI": {
        "description": "Enable GitLab Wiki support (optional, defaults to true)",
        "short": "USE_GITLAB_WIKI",
        "url": None,
        "help": "Set to 'false' to disable wiki access",
        "encrypt": False,
        "required_by": ["gitlab"],
        "optional": True,
    },
    "USE_MILESTONE": {
        "description": "Enable GitLab Milestone support (optional, defaults to true)",
        "short": "USE_MILESTONE",
        "url": None,
        "help": "Set to 'false' to disable milestone access",
        "encrypt": False,
        "required_by": ["gitlab"],
        "optional": True,
    },
    "USE_PIPELINE": {
        "description": "Enable GitLab Pipeline support (optional, defaults to true)",
        "short": "USE_PIPELINE",
        "url": None,
        "help": "Set to 'false' to disable pipeline access",
        "encrypt": False,
        "required_by": ["gitlab"],
        "optional": True,
    },
    "ATLASSIAN_API_TOKEN": {
        "description": "Atlassian API Token (for JIRA/Confluence)",
        "short": "ATLASSIAN_API_TOKEN",
        "url": "https://id.atlassian.com/manage-profile/security/api-tokens",
        "help": "Create a token at id.atlassian.com/manage-profile/security/api-tokens",
        "encrypt": True,
        "required_by": ["atlassian"],
    },
    "CONFLUENCE_URL": {
        "description": "Confluence instance URL",
        "short": "CONFLUENCE_URL",
        "url": None,
        "help": "e.g., https://yourcompany.atlassian.net/wiki",
        "encrypt": False,
        "required_by": ["atlassian"],
        "optional": True,
    },
    "CONFLUENCE_USERNAME": {
        "description": "Confluence username (usually email)",
        "short": "CONFLUENCE_USERNAME",
        "url": None,
        "help": "Your Atlassian account email",
        "encrypt": False,
        "required_by": ["atlassian"],
        "optional": True,
    },
    "CONFLUENCE_API_TOKEN": {
        "description": "Confluence API Token (same as ATLASSIAN_API_TOKEN)",
        "short": "CONFLUENCE_API_TOKEN",
        "url": "https://id.atlassian.com/manage-profile/security/api-tokens",
        "help": "Create a token at id.atlassian.com/manage-profile/security/api-tokens",
        "encrypt": True,
        "required_by": ["atlassian"],
        "optional": True,
    },
    "JIRA_URL": {
        "description": "JIRA instance URL",
        "short": "JIRA_URL",
        "url": None,
        "help": "e.g., https://yourcompany.atlassian.net",
        "encrypt": False,
        "required_by": ["atlassian"],
        "optional": True,
    },
    "JIRA_USERNAME": {
        "description": "JIRA username (usually email)",
        "short": "JIRA_USERNAME",
        "url": None,
        "help": "Your Atlassian account email",
        "encrypt": False,
        "required_by": ["atlassian"],
        "optional": True,
    },
    "GIT_AUTHOR_EMAIL": {
        "description": "Git author email (for commits)",
        "short": "GIT_AUTHOR_EMAIL",
        "url": None,
        "help": "e.g., name@example.com",
        "encrypt": False,
        "required_by": [],
        "optional": True,
    },
    "GIT_AUTHOR_NAME": {
        "description": "Git author name (for commits)",
        "short": "GIT_AUTHOR_NAME",
        "url": None,
        "help": "e.g., Your Full Name",
        "encrypt": False,
        "required_by": [],
        "optional": True,
    },
}

# Mapping of MCP server names to required env vars
MCP_SERVER_REQUIREMENTS = {
    "github": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "github-docker": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "gitlab": ["GITLAB_PERSONAL_ACCESS_TOKEN"],
    "postgres": ["POSTGRES_URL"],
    "k8s": [],  # Optional: KUBECONFIG
    "atlassian": ["ATLASSIAN_API_TOKEN"],  # Requires API token
    "duckduckgo": [],  # No env vars needed
    "filesystem": [],
    "git": [],
    "memory-bank": [],
    "redis": [],
    "docker": [],
    # Add more as needed
}


def get_required_env_vars_for_profile(profile: Profile) -> list[str]:
    """
    Get list of environment variables required by a profile.

    Args:
        profile: Profile to analyze

    Returns:
        List of env var names required by the profile
    """
    required = set()

    # Get MCPs from this profile
    for mcp_config in profile.mcp_servers:
        if not mcp_config.enabled:
            continue

        server_name = mcp_config.name
        if server_name in MCP_SERVER_REQUIREMENTS:
            required.update(MCP_SERVER_REQUIREMENTS[server_name])

    return sorted(list(required))


def get_env_var_info(env_var: str) -> dict:
    """
    Get metadata for an environment variable.

    Args:
        env_var: Environment variable name

    Returns:
        Dictionary with description, url, help text, encryption flag
    """
    if env_var in ENV_VAR_METADATA:
        return ENV_VAR_METADATA[env_var]

    # Return a default if not found
    return {
        "description": env_var,
        "short": env_var,
        "url": None,
        "help": f"Set the value for {env_var}",
        "encrypt": False,
        "required_by": [],
    }


def get_missing_env_vars(
    profile: Profile,
    env_lookup: Callable[[str], Optional[str]],
) -> list[str]:
    """
    Get list of required env vars that are missing.

    Args:
        profile: Profile to check
        env_lookup: Function to look up env vars (e.g., config_manager.get_env().get)

    Returns:
        List of missing env var names
    """
    required = get_required_env_vars_for_profile(profile)
    missing = []

    for env_var in required:
        # Check if it's already set
        if not env_lookup(env_var):
            # For GitHub, also check the alternative name
            if env_var == "GITHUB_PERSONAL_ACCESS_TOKEN":
                if env_lookup("GITHUB_TOKEN"):
                    continue
            missing.append(env_var)

    return missing


def is_env_var_optional(env_var: str) -> bool:
    """
    Check if an environment variable is optional.

    Args:
        env_var: Environment variable name

    Returns:
        True if optional, False if required
    """
    info = get_env_var_info(env_var)
    return info.get("optional", False)
