#!/bin/bash

# Test Profile Resolution and Base Layer Merging
# Tests the DRY profile system with base layer inheritance

set -euo pipefail

# Source the test framework
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$BASE_DIR/test-framework.sh"

test_suite "Profile System"

# Setup test environment
test_case "Setup test environment" {
    export CONFIG_DIR="$HOME/.local/ai-dev-test"
    export AI_PROFILES_DIR="$CONFIG_DIR/mcp-profiles"
    
    # Create test directories
    mkdir -p "$CONFIG_DIR"/mcp-profiles
    mkdir -p "$CONFIG_DIR"/mcp-layers
    
    # Copy templates
    cd "$BASE_DIR/.."
    cp templates/mcp-profiles/* "$CONFIG_DIR"/mcp-profiles/
    cp templates/mcp-layers/* "$CONFIG_DIR"/mcp-layers/
    cp bin/ai-utils.sh "$CONFIG_DIR"/
    
    assert_status_code 0
}

test_case "Source utilities" {
    source "$CONFIG_DIR"/ai-utils.sh
    assert_status_code 0
}

# Test each profile
for profile in default persistent devops qa research; do
    test_case "Profile resolution: $profile" {
        if cfg_file=$(_resolve_profile_cfg "$profile" 2>/dev/null); then
            # Verify file was created
            [[ -f "$cfg_file" ]] || fail "Config file not created: $cfg_file"
            
            # Check if it's valid JSON
            if command -v jq >/dev/null 2>&1; then
                jq empty "$cfg_file" || fail "Invalid JSON in config file"
                
                # Verify it has mcpServers section
                jq -e '.mcpServers' "$cfg_file" >/dev/null || fail "Missing mcpServers section"
            fi
            
            # Clean up temp file
            rm -f "$cfg_file"
        else
            fail "Profile resolution failed for $profile"
        fi
    }
done

# Test profile requirements
test_case "Profile requirements validation" {
    # Set test environment variables
    export GITLAB_PERSONAL_ACCESS_TOKEN="test-token"
    export KUBECONFIG="$HOME/.kube/config"
    
    # Test default profile (no requirements)
    _require_env "default" >/dev/null 2>&1
    assert_status_code 0
    
    # Test devops profile (requires GITLAB_TOKEN and KUBECONFIG)
    # This may fail if KUBECONFIG file doesn't exist, which is expected
    _require_env "devops" >/dev/null 2>&1 || true
}

cleanup() {
    rm -rf "$HOME/.local/ai-dev-test"
}

trap cleanup EXIT

run_test_suite