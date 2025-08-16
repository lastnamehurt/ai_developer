#!/bin/bash

# Test Installation Simulation
# Tests the complete installation process by simulating what happens
# when users install via curl from the repository

set -euo pipefail

# Source the test framework
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$BASE_DIR/test-framework.sh"

test_suite "Installation Simulation"

test_case "Clean install location" {
    # Clean install location
    rm -rf ~/.local/ai-dev-test
    mkdir -p ~/.local/ai-dev-test
    assert_status_code 0
}

test_case "Copy core files" {
    # Copy all necessary files
    cd "$BASE_DIR/.."
    cp -r bin ~/.local/ai-dev-test/
    cp -r templates ~/.local/ai-dev-test/
    cp -r docs ~/.local/ai-dev-test/
    cp install.sh ~/.local/ai-dev-test/
    cp README.md ~/.local/ai-dev-test/
    cp CLAUDE.md ~/.local/ai-dev-test/
    assert_status_code 0
}

test_case "Create environment template" {
    # Create .env template
    cat > ~/.local/ai-dev-test/.env << 'EOF'
# AI Development Environment Variables
GITLAB_PERSONAL_ACCESS_TOKEN=test-token
GITLAB_API_URL=https://gitlab.example.com/api/v4
KUBECONFIG=${HOME}/.kube/config
MEMORY_BANK_ROOT=${HOME}/.local/ai-dev-test/memory-banks
GIT_AUTHOR_NAME="Test User"
GIT_AUTHOR_EMAIL="test@example.com"
EOF
    assert_status_code 0
    assert_file_exists ~/.local/ai-dev-test/.env
}

test_case "Setup MCP profiles" {
    # Copy profile templates
    mkdir -p ~/.local/ai-dev-test/mcp-profiles
    cp templates/mcp-profiles/* ~/.local/ai-dev-test/mcp-profiles/
    assert_status_code 0
    assert_directory_exists ~/.local/ai-dev-test/mcp-profiles
}

test_case "Setup base layers" {
    # Copy base layers
    mkdir -p ~/.local/ai-dev-test/mcp-layers
    cp templates/mcp-layers/* ~/.local/ai-dev-test/mcp-layers/
    assert_status_code 0
    assert_directory_exists ~/.local/ai-dev-test/mcp-layers
}

test_case "Create default profile symlink" {
    # Create default profile symlink
    cd ~/.local/ai-dev-test
    ln -sf mcp-profiles/default.mcp.json mcp.json
    assert_status_code 0
    assert_file_exists ~/.local/ai-dev-test/mcp.json
}

test_case "Make scripts executable" {
    # Make ai command executable
    chmod +x ~/.local/ai-dev-test/bin/ai*
    assert_status_code 0
    [[ -x ~/.local/ai-dev-test/bin/ai ]] || fail "ai command not executable"
}

test_case "Test basic functionality" {
    # Test help command
    ~/.local/ai-dev-test/bin/ai help >/dev/null
    assert_status_code 0
    
    # Test check command (may warn about missing tools)
    ~/.local/ai-dev-test/bin/ai check >/dev/null 2>&1 || true
    # Always passes since check may fail due to missing tools
}

cleanup() {
    rm -rf ~/.local/ai-dev-test
}

trap cleanup EXIT

run_test_suite