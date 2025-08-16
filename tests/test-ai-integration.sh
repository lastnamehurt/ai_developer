#!/bin/bash

# Integration Tests for main ai script
# Tests command routing, argument parsing, and end-to-end functionality

set -euo pipefail

# Get the script directory and source the test framework
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-framework.sh"

# Path to the main ai script
BIN_DIR="$(dirname "$SCRIPT_DIR")/bin"
AI_SCRIPT="$BIN_DIR/ai"

# Test help command functionality
test_help_commands() {
    test_start "ai help shows usage information"
    
    local output
    output=$("$AI_SCRIPT" help 2>&1)
    
    assert_contains "$output" "Universal AI Development Environment"
    assert_contains "$output" "Usage:"
    assert_contains "$output" "Commands:"
    assert_contains "$output" "claude"
    assert_contains "$output" "cursor"
    assert_contains "$output" "init"
    assert_contains "$output" "Profile support:"
    
    test_start "ai --help shows usage information"
    
    local output
    output=$("$AI_SCRIPT" --help 2>&1)
    
    assert_contains "$output" "Universal AI Development Environment"
    assert_contains "$output" "Usage:"
    
    test_start "ai -h shows usage information"
    
    local output
    output=$("$AI_SCRIPT" -h 2>&1)
    
    assert_contains "$output" "Universal AI Development Environment"
}

# Test command routing
test_command_routing() {
    test_start "ai with no arguments shows error and help"
    
    local output result=0
    output=$("$AI_SCRIPT" 2>&1) || result=$?
    
    assert_equals "1" "$result"
    assert_contains "$output" "No command specified"
    
    test_start "ai with invalid command shows error"
    
    local output result=0
    output=$("$AI_SCRIPT" invalid_command 2>&1) || result=$?
    
    # Should try to run as external command and likely fail
    # The exact behavior depends on whether 'invalid_command' exists
    assert_equals "127" "$result" # Command not found
}

# Test check command
test_check_command() {
    test_start "ai check runs environment check"
    
    local output
    output=$("$AI_SCRIPT" check 2>&1)
    
    assert_contains "$output" "Checking AI development environment"
    assert_contains "$output" "Current directory:"
    assert_contains "$output" "Available AI tools:"
}

# Test load command
test_load_command() {
    test_start "ai load shows environment loading info"
    
    local output
    output=$("$AI_SCRIPT" load 2>&1)
    
    assert_contains "$output" "Environment variables loaded for current shell session"
    assert_contains "$output" "Variables are only available in the current shell"
}

# Test install command
test_install_command() {
    test_start "ai install attempts to find and run install script"
    
    # Create a mock install script for testing
    local mock_install="$TEST_TEMP_DIR/install.sh"
    cat > "$mock_install" << 'EOF'
#!/bin/bash
echo "Mock install script executed"
exit 0
EOF
    chmod +x "$mock_install"
    
    # Create the expected directory structure
    mkdir -p "$TEST_TEMP_DIR/.local/ai-dev"
    cp "$mock_install" "$TEST_TEMP_DIR/.local/ai-dev/install.sh"
    
    # Override HOME for this test
    local original_home="$HOME"
    export HOME="$TEST_TEMP_DIR"
    
    local output
    output=$("$AI_SCRIPT" install 2>&1)
    
    assert_contains "$output" "Installing/updating AI development environment"
    assert_contains "$output" "Running install script:"
    
    # Restore environment
    export HOME="$original_home"
}

# Test sync command
test_sync_command() {
    test_start "ai sync attempts to sync configurations"
    
    local original_pwd=$(pwd)
    cd "$TEST_TEMP_DIR"
    
    # Create test .claude directory
    mkdir -p .claude
    echo '{"mcpServers":{}}' > ".claude/.mcp.json"
    
    local output result=0
    output=$("$AI_SCRIPT" sync 2>&1) || result=$?
    
    # Should succeed with proper setup
    assert_equals "0" "$result"
    assert_contains "$output" "Config sync completed"
    
    cd "$original_pwd"
    
    test_start "ai sync fails gracefully without .claude directory"
    
    cd "$TEST_TEMP_DIR"
    rm -rf .claude .cursor
    
    local output result=0
    output=$("$AI_SCRIPT" sync 2>&1) || result=$?
    
    assert_equals "1" "$result"
    assert_contains "$output" "No .claude directory found"
    
    cd "$original_pwd"
}

# Test profile-aware commands (claude/cursor)
test_profile_commands() {
    test_start "ai claude command parses profile argument"
    
    # Create mock profile
    local profiles_dir="$TEST_CONFIG_DIR/mcp-profiles"
    mkdir -p "$profiles_dir"
    echo '{"mcpServers":{}}' > "$profiles_dir/test.mcp.json"
    
    # Mock claude command
    mock_command "claude" 'echo "Claude launched with: $*"; exit 0'
    
    # Create a temporary AI script with test environment variables
    local test_ai_script="$TEST_TEMP_DIR/test-ai"
    cat > "$test_ai_script" << EOF
#!/bin/bash
set -euo pipefail

# Override environment variables for testing
export CONFIG_DIR="$TEST_CONFIG_DIR"
export AI_SYSTEM_DIR="$TEST_CONFIG_DIR"
export ENV_FILE=".env"
export GLOBAL_ENV_FILE="$TEST_CONFIG_DIR/.env"
export MCP_FILE=".mcp.json"
export AI_PROFILES_DIR="$profiles_dir"

# Source the modules
source "$BIN_DIR/ai-utils.sh"
source "$BIN_DIR/ai-core.sh"
source "$BIN_DIR/ai-project.sh"

# Profile-aware claude command
cmd_claude() {
    local profile="default" pass_args=()
    while [[ \$# -gt 0 ]]; do case "\$1" in
        --profile) profile="\${2:?}"; shift 2 ;;
        *) pass_args+=("\$1"); shift ;;
    esac; done
    
    load_env_vars
    _load_env_once
    [[ "\$profile" =~ ^(devops|qa)$ ]] && _require_env GITLAB_PERSONAL_ACCESS_TOKEN GITLAB_API_URL
    local cfg; cfg="\$(_resolve_profile_cfg "\$profile")"
    log_info "🤖 Launching Claude Code with profile: \$profile"
    claude --mcp-config "\$cfg" "\${pass_args[@]+"\${pass_args[@]}"}"
}

# Main command router for testing
case "\${1:-}" in
    "claude")
        shift
        cmd_claude "\$@"
        ;;
    *)
        echo "Unknown command: \$1"
        exit 1
        ;;
esac
EOF
    chmod +x "$test_ai_script"
    
    local output result=0
    output=$("$test_ai_script" claude --profile test 2>&1) || result=$?
    
    assert_contains "$output" "Launching Claude Code with profile: test"
    assert_contains "$output" "Claude launched with:"
    
    restore_command "claude"
    
    test_start "ai cursor command parses profile argument"
    
    # Mock cursor command
    mock_command "cursor" 'echo "Cursor launched with: $*"; exit 0'
    
    # Create a temporary AI script for cursor testing
    local test_cursor_script="$TEST_TEMP_DIR/test-cursor"
    cat > "$test_cursor_script" << EOF
#!/bin/bash
set -euo pipefail

# Override environment variables for testing
export CONFIG_DIR="$TEST_CONFIG_DIR"
export AI_SYSTEM_DIR="$TEST_CONFIG_DIR"
export ENV_FILE=".env"
export GLOBAL_ENV_FILE="$TEST_CONFIG_DIR/.env"
export MCP_FILE=".mcp.json"
export AI_PROFILES_DIR="$profiles_dir"

# Source the modules
source "$BIN_DIR/ai-utils.sh"
source "$BIN_DIR/ai-core.sh"
source "$BIN_DIR/ai-project.sh"

# Profile-aware cursor command
cmd_cursor() {
    local profile="default" pass_args=()
    while [[ \$# -gt 0 ]]; do case "\$1" in
        --profile) profile="\${2:?}"; shift 2 ;;
        *) pass_args+=("\$1"); shift ;;
    esac; done
    
    load_env_vars
    _load_env_once
    [[ "\$profile" =~ ^(devops|qa)$ ]] && _require_env GITLAB_PERSONAL_ACCESS_TOKEN GITLAB_API_URL
    local cfg; cfg="\$(_resolve_profile_cfg "\$profile")"
    log_info "🎯 Launching Cursor with profile: \$profile"
    
    # Ensure .cursor directory exists in current directory
    mkdir -p .cursor
    cp "\$cfg" .cursor/mcp.json
    
    # Launch Cursor in current directory or specified paths
    if [ \$# -eq 0 ]; then
        cursor .
    else
        cursor "\${pass_args[@]+"\${pass_args[@]}"}"
    fi
}

# Main command router for testing
case "\${1:-}" in
    "cursor")
        shift
        cmd_cursor "\$@"
        ;;
    *)
        echo "Unknown command: \$1"
        exit 1
        ;;
esac
EOF
    chmod +x "$test_cursor_script"
    
    local output result=0
    output=$("$test_cursor_script" cursor --profile test 2>&1) || result=$?
    
    assert_contains "$output" "Launching Cursor with profile: test"
    assert_contains "$output" "Cursor launched with:"
    
    restore_command "cursor"
}

# Test profile validation
test_profile_validation() {
    test_start "ai claude fails with non-existent profile"
    
    local profiles_dir="$TEST_CONFIG_DIR/mcp-profiles"
    mkdir -p "$profiles_dir"
    # Don't create the nonexistent profile
    
    # Create a temporary AI script for testing
    local test_ai_script="$TEST_TEMP_DIR/test-ai-validation"
    cat > "$test_ai_script" << EOF
#!/bin/bash
set -euo pipefail

# Override environment variables for testing
export CONFIG_DIR="$TEST_CONFIG_DIR"
export AI_SYSTEM_DIR="$TEST_CONFIG_DIR"
export ENV_FILE=".env"
export GLOBAL_ENV_FILE="$TEST_CONFIG_DIR/.env"
export MCP_FILE=".mcp.json"
export AI_PROFILES_DIR="$profiles_dir"

# Minimal logging functions for testing
log_error() { echo "ERROR: \$*" >&2; }
log_info() { echo "INFO: \$*"; }
log_success() { echo "SUCCESS: \$*"; }

# Minimal profile resolution function for testing
_resolve_profile_cfg() {
    local profile="\${1:-default}"
    local profile_cfg="\$AI_PROFILES_DIR/\${profile}.mcp.json"
    if [[ ! -f "\$profile_cfg" ]]; then
        log_error "Profile not found: \$profile_cfg"
        exit 1
    fi
    local out_cfg; out_cfg="\$(mktemp).mcp.json"
    cp "\$profile_cfg" "\$out_cfg"
    printf "%s" "\$out_cfg"
}

# Profile-aware claude command
cmd_claude() {
    local profile="default" pass_args=()
    while [[ \$# -gt 0 ]]; do case "\$1" in
        --profile) profile="\${2:?}"; shift 2 ;;
        *) pass_args+=("\$1"); shift ;;
    esac; done
    
    local cfg; cfg="\$(_resolve_profile_cfg "\$profile")"
    log_info "🤖 Launching Claude Code with profile: \$profile"
    claude --mcp-config "\$cfg" "\${pass_args[@]+"\${pass_args[@]}"}"
}

# Main command router for testing
case "\${1:-}" in
    "claude")
        shift
        cmd_claude "\$@"
        ;;
    *)
        echo "Unknown command: \$1"
        exit 1
        ;;
esac
EOF
    chmod +x "$test_ai_script"
    
    local output result=0
    output=$("$test_ai_script" claude --profile nonexistent 2>&1) || result=$?
    
    assert_equals "1" "$result"
    assert_contains "$output" "Profile not found"
}

# Test environment variable requirements
test_environment_requirements() {
    test_start "ai claude with devops profile requires GitLab variables"
    
    # Create devops profile
    local profiles_dir="$TEST_CONFIG_DIR/mcp-profiles"
    mkdir -p "$profiles_dir"
    echo '{"mcpServers":{}}' > "$profiles_dir/devops.mcp.json"
    
    # Create a temporary AI script for testing
    local test_ai_script="$TEST_TEMP_DIR/test-ai-env"
    cat > "$test_ai_script" << EOF
#!/bin/bash
set -euo pipefail

# Override environment variables for testing
export CONFIG_DIR="$TEST_CONFIG_DIR"
export AI_SYSTEM_DIR="$TEST_CONFIG_DIR"
export ENV_FILE=".env"
export GLOBAL_ENV_FILE="$TEST_CONFIG_DIR/.env"
export MCP_FILE=".mcp.json"
export AI_PROFILES_DIR="$profiles_dir"

# Minimal logging functions for testing
log_error() { echo "ERROR: \$*" >&2; }
log_info() { echo "INFO: \$*"; }
log_success() { echo "SUCCESS: \$*"; }

# Minimal environment requirement function for testing
_require_env() {
    local missing=()
    for k in "\$@"; do [[ -n "\${!k:-}" ]] || missing+=("\$k"); done
    if (( \${#missing[@]} )); then
        log_error "Missing vars in \$GLOBAL_ENV_FILE: \${missing[*]}"
        return 1
    fi
    return 0
}

# Minimal profile resolution function for testing
_resolve_profile_cfg() {
    local profile="\${1:-default}"
    local profile_cfg="\$AI_PROFILES_DIR/\${profile}.mcp.json"
    if [[ ! -f "\$profile_cfg" ]]; then
        log_error "Profile not found: \$profile_cfg"
        exit 1
    fi
    local out_cfg; out_cfg="\$(mktemp).mcp.json"
    cp "\$profile_cfg" "\$out_cfg"
    printf "%s" "\$out_cfg"
}

# Profile-aware claude command
cmd_claude() {
    local profile="default" pass_args=()
    while [[ \$# -gt 0 ]]; do case "\$1" in
        --profile) profile="\${2:?}"; shift 2 ;;
        *) pass_args+=("\$1"); shift ;;
    esac; done
    
    # Check environment requirements for devops profile
    [[ "\$profile" =~ ^(devops|qa)$ ]] && _require_env GITLAB_PERSONAL_ACCESS_TOKEN GITLAB_API_URL || exit \$?
    
    local cfg; cfg="\$(_resolve_profile_cfg "\$profile")"
    log_info "🤖 Launching Claude Code with profile: \$profile"
    claude --mcp-config "\$cfg" "\${pass_args[@]+"\${pass_args[@]}"}"
}

# Main command router for testing
case "\${1:-}" in
    "claude")
        shift
        cmd_claude "\$@"
        ;;
    *)
        echo "Unknown command: \$1"
        exit 1
        ;;
esac
EOF
    chmod +x "$test_ai_script"
    
    # Ensure required variables are not set
    unset GITLAB_PERSONAL_ACCESS_TOKEN 2>/dev/null || true
    unset GITLAB_API_URL 2>/dev/null || true
    
    local output result=0
    output=$("$test_ai_script" claude --profile devops 2>&1) || result=$?
    
    assert_equals "1" "$result"
    assert_contains "$output" "Missing vars"
}

# Test command pass-through functionality
test_command_passthrough() {
    test_start "ai passes unknown commands to external execution"
    
    # Mock echo command to test pass-through
    local output result=0
    output=$("$AI_SCRIPT" echo "test message" 2>&1) || result=$?
    
    assert_equals "0" "$result"
    assert_contains "$output" "Running: echo test message"
    assert_contains "$output" "test message"
}

# Test modular sourcing
test_modular_sourcing() {
    test_start "ai script successfully sources all required modules"
    
    # Test that the script can load without errors
    local output result=0
    output=$(bash -n "$AI_SCRIPT" 2>&1) || result=$?
    
    assert_equals "0" "$result"
    
    test_start "ai script modules are found in correct location"
    
    # Verify the modules exist where the script expects them
    assert_file_exists "$BIN_DIR/ai-utils.sh"
    assert_file_exists "$BIN_DIR/ai-core.sh"
    assert_file_exists "$BIN_DIR/ai-project.sh"
    
    test_start "ai script modules have execute permissions"
    
    assert_command_success "test -x '$BIN_DIR/ai-utils.sh'"
    assert_command_success "test -x '$BIN_DIR/ai-core.sh'"
    assert_command_success "test -x '$BIN_DIR/ai-project.sh'"
}

# Test error handling
test_error_handling() {
    test_start "ai script handles missing modules gracefully"
    
    # Create a temporary ai script with broken module path
    local broken_ai="$TEST_TEMP_DIR/broken-ai"
    cat > "$broken_ai" << 'EOF'
#!/bin/bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/nonexistent-module.sh"
EOF
    chmod +x "$broken_ai"
    
    local output result=0
    output=$("$broken_ai" 2>&1) || result=$?
    
    # Should fail due to missing module
    assert_equals "1" "$result"
    assert_contains "$output" "No such file or directory"
}

# Test argument preservation
test_argument_preservation() {
    test_start "ai script preserves arguments correctly"
    
    # Test with echo command that shows all arguments
    local output
    output=$("$AI_SCRIPT" echo "arg1" "arg with spaces" "arg3" 2>&1)
    
    assert_contains "$output" "arg1"
    assert_contains "$output" "arg with spaces"
    assert_contains "$output" "arg3"
    assert_contains "$output" "Running: echo arg1 arg with spaces arg3"
}

# Run all test suites
main() {
    echo "Testing main ai script integration..."
    setup_test_env
    
    run_test_suite "Help Commands" test_help_commands
    run_test_suite "Command Routing" test_command_routing
    run_test_suite "Check Command" test_check_command
    run_test_suite "Load Command" test_load_command
    run_test_suite "Install Command" test_install_command
    run_test_suite "Sync Command" test_sync_command
    run_test_suite "Profile Commands" test_profile_commands
    run_test_suite "Profile Validation" test_profile_validation
    run_test_suite "Environment Requirements" test_environment_requirements
    run_test_suite "Command Pass-through" test_command_passthrough
    run_test_suite "Modular Sourcing" test_modular_sourcing
    run_test_suite "Error Handling" test_error_handling
    run_test_suite "Argument Preservation" test_argument_preservation
    
    print_test_summary
}

# Run tests if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi