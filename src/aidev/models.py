"""
Pydantic models for aidev configuration and data structures
"""
from typing import Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class MCPServerConfig(BaseModel):
    """MCP Server configuration"""
    name: str
    enabled: bool = True
    config: dict[str, Any] = Field(default_factory=dict)


class ToolConfig(BaseModel):
    """AI tool configuration"""
    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)


class Profile(BaseModel):
    """AI development profile"""
    name: str
    description: str
    extends: Optional[str] = None
    mcp_servers: list[MCPServerConfig] = Field(default_factory=list)
    environment: dict[str, str] = Field(default_factory=dict)
    tools: dict[str, ToolConfig] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate profile name"""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Profile name must be alphanumeric (with - or _ allowed)")
        return v


class MCPServerRegistry(BaseModel):
    """MCP Server registry entry"""
    name: str
    description: str
    author: str
    repository: str
    version: str
    install: dict[str, str]
    configuration: dict[str, list[str]] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    """Project-specific configuration"""
    profile: Optional[str] = None
    environment: dict[str, str] = Field(default_factory=dict)
    mcp_overrides: dict[str, Any] = Field(default_factory=dict)


class ToolInfo(BaseModel):
    """Information about an installed AI tool"""
    name: str
    binary: str
    app_name: str
    config_path: Path
    installed: bool = False
    version: Optional[str] = None


class BackupManifest(BaseModel):
    """Backup manifest metadata"""
    version: str
    created_at: str
    hostname: str
    profiles: list[str]
    mcp_servers: list[str]
    has_env: bool
