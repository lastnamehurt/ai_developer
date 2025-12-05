#!/usr/bin/env python3
"""
Test MCP config generation
"""
from pathlib import Path
from aidev.profiles import ProfileManager
from aidev.mcp_config_generator import MCPConfigGenerator
from aidev.tools import ToolManager

# Initialize managers
profile_manager = ProfileManager()
mcp_config_generator = MCPConfigGenerator()
tool_manager = ToolManager()

# Load default profile
print("Loading default profile...")
profile = profile_manager.load_profile("default")
if not profile:
    print("ERROR: Could not load default profile")
    exit(1)

print(f"Profile loaded: {profile.name}")
print(f"MCP servers in profile: {[s.name for s in profile.mcp_servers if s.enabled]}")

# Test config generation for Claude Code
tool_id = "claude"
print(f"\nGenerating MCP config for {tool_id}...")
tool_config_path = tool_manager.get_tool_config_path(tool_id)
print(f"Config path: {tool_config_path}")

mcp_config_generator.generate_config(tool_id, profile, tool_config_path)

# Verify the file exists
if tool_config_path.exists():
    print(f"\n✓ Config file created successfully!")
    import json
    with open(tool_config_path) as f:
        config = json.load(f)
    print(f"\nGenerated config:")
    print(json.dumps(config, indent=2))
else:
    print(f"\nERROR: Config file was not created at {tool_config_path}")

# Test for Cursor as well
print("\n" + "="*60)
tool_id = "cursor"
print(f"Generating MCP config for {tool_id}...")
tool_config_path = tool_manager.get_tool_config_path(tool_id)
print(f"Config path: {tool_config_path}")

mcp_config_generator.generate_config(tool_id, profile, tool_config_path)

if tool_config_path.exists():
    print(f"\n✓ Config file created successfully!")
    with open(tool_config_path) as f:
        config = json.load(f)
    print(f"\nGenerated config:")
    print(json.dumps(config, indent=2))
else:
    print(f"\nERROR: Config file was not created at {tool_config_path}")
