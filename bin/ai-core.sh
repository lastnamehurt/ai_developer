#!/bin/bash

# AI Development Environment - Core Functions
# This module contains core environment loading and profile management functions

# Source utility functions
source "$(dirname "${BASH_SOURCE[0]}")/ai-utils.sh"

# Load environment variables
load_env_vars() {
    # Load global environment variables first
    load_env_from_file "$GLOBAL_ENV_FILE" "global config ($GLOBAL_ENV_FILE)"
    
    # Load local environment variables (these can override global ones)
    load_env_from_file "$ENV_FILE" "local config ($(pwd)/$ENV_FILE)"
}

# Load environment for current shell session
load_env_for_shell() {
    load_env_vars
    log_info "Environment variables loaded for current shell session"
    log_warning "Note: Variables are only available in the current shell"
    echo "Run 'env | grep -E \"(DD_|DATADOG|GITLAB|ATLASSIAN|JIRA|CONFLUENCE)\"' to see loaded variables"
}

# Check environment setup
check_environment() {
    log_info "Checking AI development environment..."
    
    echo "📁 Current directory: $(pwd)"
    
    # Check global environment file
    if [[ -f "$GLOBAL_ENV_FILE" ]]; then
        local global_var_count=$(grep -c "^[A-Za-z_][A-Za-z0-9_]*=" "$GLOBAL_ENV_FILE" 2>/dev/null || echo "0")
        log_success "Global env file found with $global_var_count variables ($GLOBAL_ENV_FILE)"
    else
        log_warning "Global env file not found ($GLOBAL_ENV_FILE)"
    fi
    
    # Check local environment file
    if [[ -f "$ENV_FILE" ]]; then
        local var_count=$(grep -c "^[A-Za-z_][A-Za-z0-9_]*=" "$ENV_FILE" 2>/dev/null || echo "0")
        log_success "Local env file found with $var_count variables ($ENV_FILE)"
    else
        log_warning "Local env file not found ($ENV_FILE)"
    fi
    
    # Check local MCP files
    local mcp_found=false
    if [[ -f ".claude/.mcp.json" ]]; then
        if [[ -L ".claude/.mcp.json" ]]; then
            log_success ".claude/.mcp.json found (symlinked to global config)"
        else
            log_success ".claude/.mcp.json found (local config)"
        fi
        mcp_found=true
    fi
    
    if [[ -f ".cursor/mcp.json" ]]; then
        if [[ -L ".cursor/mcp.json" ]]; then
            log_success ".cursor/mcp.json found (symlinked to global config)"
        else
            log_success ".cursor/mcp.json found (local config)"
        fi
        mcp_found=true
    fi
    
    if [[ -f "$MCP_FILE" ]]; then
        log_success ".mcp.json found (root level config)"
        mcp_found=true
    fi
    
    if [[ "$mcp_found" == "false" ]]; then
        log_warning "No MCP config files found (run 'ai init' to create them)"
    fi
    
    # Check profiles
    if [[ -d "$AI_PROFILES_DIR" ]]; then
        local profile_count=0
        for profile in "$AI_PROFILES_DIR"/*.mcp.json; do
            if [[ -f "$profile" ]]; then
                ((profile_count++))
            fi
        done
        log_success "Found $profile_count MCP profiles in $AI_PROFILES_DIR"
        if [[ -f "$CONFIG_DIR/mcp.json" && -L "$CONFIG_DIR/mcp.json" ]]; then
            local current_profile=$(readlink "$CONFIG_DIR/mcp.json" | sed 's/.*\/\([^/]*\)\.mcp\.json/\1/')
            log_info "Current default profile: $current_profile"
        fi
    else
        log_warning "MCP profiles directory not found ($AI_PROFILES_DIR)"
    fi
    
    # Check for available tools
    echo ""
    log_info "Available AI tools:"
    
    if command -v claude >/dev/null 2>&1 && claude --help >/dev/null 2>&1; then
        echo "  ✅ Claude Code"
    else
        echo "  ❌ Claude Code (not installed)"
    fi
    
    if command -v cursor >/dev/null 2>&1 && cursor --help >/dev/null 2>&1; then
        echo "  ✅ Cursor"
    else
        echo "  ❌ Cursor (not installed)"
    fi
    
    # Show available profiles
    if [[ -d "$AI_PROFILES_DIR" ]]; then
        echo ""
        log_info "Available MCP profiles:"
        for profile in "$AI_PROFILES_DIR"/*.mcp.json; do
            if [[ -f "$profile" ]]; then
                local name=$(basename "$profile" .mcp.json)
                echo "  📋 $name"
            fi
        done
    fi
}
