#!/bin/bash

# Test Claude Sub Agents Setup
# Tests the creation and configuration of Sub Agents

set -euo pipefail

# Source the test framework
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$BASE_DIR/test-framework.sh"

test_suite "Claude Sub Agents"

# Create test project
test_case "Setup test project" {
    rm -rf test-agents-project
    mkdir test-agents-project
    cd test-agents-project
    assert_status_code 0
}

test_case "Setup test environment" {
    # Setup test ai-dev installation
    export CONFIG_DIR="$HOME/.local/ai-dev-test"
    mkdir -p "$CONFIG_DIR"/bin
    mkdir -p "$CONFIG_DIR"/templates/agents
    
    # Copy necessary files
    cd "$BASE_DIR/.."
    cp bin/ai "$CONFIG_DIR"/bin/
    cp bin/ai-project.sh "$CONFIG_DIR"/bin/
    cp bin/ai-utils.sh "$CONFIG_DIR"/bin/
    cp bin/ai-core.sh "$CONFIG_DIR"/bin/
    cp -r templates/agents/* "$CONFIG_DIR"/templates/agents/
    
    chmod +x "$CONFIG_DIR"/bin/*
    
    assert_status_code 0
}

test_case "Run ai init with test config" {
    cd test-agents-project
    
    # Use test config location
    CONFIG_DIR="$HOME/.local/ai-dev-test" "$CONFIG_DIR"/bin/ai init >/dev/null 2>&1
    assert_status_code 0
}

test_case "Verify agents directory created" {
    [[ -d ".claude/agents" ]] || fail ".claude/agents directory not created"
}

# Test each expected agent
agents=(
    "devops-deployer.md"
    "qa-test-runner.md"
    "core-dev-reviewer.md"
    "research-synthesizer.md"
)

for agent in "${agents[@]}"; do
    test_case "Verify agent: $agent" {
        [[ -f ".claude/agents/$agent" ]] || fail "Agent file missing: $agent"
        
        # Check for YAML frontmatter
        head -n 1 ".claude/agents/$agent" | grep -q "^---$" || fail "Missing YAML frontmatter in $agent"
        
        # Check for name field
        grep -q "^name:" ".claude/agents/$agent" || fail "Missing name field in $agent"
        
        # Check for description field
        grep -q "^description:" ".claude/agents/$agent" || fail "Missing description field in $agent"
    }
done

test_case "Verify agent content" {
    # Check one agent has proper content
    agent_file=".claude/agents/devops-deployer.md"
    
    # Should contain YAML frontmatter and content
    [[ $(wc -l < "$agent_file") -gt 10 ]] || fail "Agent file too short: $agent_file"
    
    # Should contain deployment-related content
    grep -qi "deployment\|kubernetes\|kubectl" "$agent_file" || fail "Missing deployment content in $agent_file"
}

cleanup() {
    cd "$BASE_DIR"
    rm -rf test-agents-project
    rm -rf "$HOME/.local/ai-dev-test"
}

trap cleanup EXIT

run_test_suite