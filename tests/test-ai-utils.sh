#!/bin/bash

# Tests for ai-utils.sh
# Tests utility functions like logging, validation, and helpers

set -euo pipefail

# Get the script directory and source the test framework
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/test-framework.sh"

# Source the module under test
BIN_DIR="$(dirname "$SCRIPT_DIR")/bin"
source "$BIN_DIR/ai-utils.sh"

# Test the logging functions
test_logging_functions() {
    test_start "log_info produces correct output"
    local output=$(log_info "test message" 2>&1)
    assert_contains "$output" "ℹ️"
    assert_contains "$output" "test message"
    
    test_start "log_success produces correct output"
    local output=$(log_success "success message" 2>&1)
    assert_contains "$output" "✅"
    assert_contains "$output" "success message"
    
    test_start "log_warning produces correct output"
    local output=$(log_warning "warning message" 2>&1)
    assert_contains "$output" "⚠️"
    assert_contains "$output" "warning message"
    
    test_start "log_error produces correct output"
    local output=$(log_error "error message" 2>&1)
    assert_contains "$output" "❌"
    assert_contains "$output" "error message"
}

# Test jq checking function
test_check_jq_function() {
    test_start "check_jq returns success when jq is available"
    # Mock jq command to be available
    mock_command "jq" "exit 0"
    assert_command_success "check_jq"
    restore_command "jq"
    
    test_start "check_jq attempts installation when jq unavailable and brew available"
    # Mock commands
    mock_command "jq" "exit 1"  # jq not found initially
    mock_command "brew" "echo 'installing jq...'; exit 0"
    
    # check_jq should succeed (return 0) when brew is available
    local result=0
    check_jq >/dev/null 2>&1 || result=$?
    assert_equals "0" "$result"
    
    restore_command "jq"
    restore_command "brew"
    
    test_start "check_jq fails gracefully when neither jq nor brew available"
    # Remove both jq and brew from PATH to simulate them not being available
    local original_path="$PATH"
    export PATH="/bin:/usr/sbin:/sbin"  # Minimal PATH without /usr/bin (no jq) and no homebrew
    
    # Debug: check what commands are available
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Debug: PATH=$PATH"
        echo "Debug: command -v jq: $(command -v jq || echo 'not found')"
        echo "Debug: command -v brew: $(command -v brew || echo 'not found')"
    fi
    
    local result=0
    check_jq >/dev/null 2>&1 || result=$?
    assert_equals "1" "$result"
    
    # Restore original PATH
    export PATH="$original_path"
}

# Test environment validation function
test_require_env_function() {
    test_start "_require_env passes when all variables are set"
    export TEST_VAR1="value1"
    export TEST_VAR2="value2"
    assert_command_success "_require_env TEST_VAR1 TEST_VAR2"
    unset TEST_VAR1 TEST_VAR2
    
    test_start "_require_env fails when variables are missing"
    unset TEST_MISSING_VAR 2>/dev/null || true
    assert_command_fails "_require_env TEST_MISSING_VAR"
    
    test_start "_require_env fails with empty variables"
    export TEST_EMPTY_VAR=""
    assert_command_fails "_require_env TEST_EMPTY_VAR"
    unset TEST_EMPTY_VAR
}

# Test load_env_from_file function
test_load_env_from_file_function() {
    test_start "load_env_from_file loads variables from file"
    local test_env_file="$TEST_TEMP_DIR/test.env"
    cat > "$test_env_file" << EOF
# This is a comment
TEST_VAR1=value1
TEST_VAR2="value with spaces"
TEST_VAR3='single quotes'

# Another comment
TEST_VAR4=value4
EOF
    
    load_env_from_file "$test_env_file" "test env"
    
    assert_equals "value1" "$TEST_VAR1"
    assert_equals "value with spaces" "$TEST_VAR2"
    assert_equals "single quotes" "$TEST_VAR3"
    assert_equals "value4" "$TEST_VAR4"
    
    # Clean up
    unset TEST_VAR1 TEST_VAR2 TEST_VAR3 TEST_VAR4
    
    test_start "load_env_from_file handles non-existent file gracefully"
    assert_command_success "load_env_from_file /nonexistent/file.env 'test'"
    
    test_start "load_env_from_file skips invalid lines"
    local invalid_env_file="$TEST_TEMP_DIR/invalid.env"
    cat > "$invalid_env_file" << EOF
VALID_VAR=value
invalid line without equals
=invalid_variable_name
ANOTHER_VALID=another_value
EOF
    
    load_env_from_file "$invalid_env_file" "invalid test"
    
    assert_equals "value" "$VALID_VAR"
    assert_equals "another_value" "$ANOTHER_VALID"
    
    unset VALID_VAR ANOTHER_VALID
}

# Test find_templates_dir function
test_find_templates_dir_function() {
    test_start "find_templates_dir finds existing templates directory"
    
    # Create mock directories
    local mock_templates="$TEST_TEMP_DIR/templates"
    local mock_docs="$TEST_TEMP_DIR/docs"
    mkdir -p "$mock_templates"
    mkdir -p "$mock_docs"
    touch "$mock_docs/engineering-workflow.md"
    
    # Override CONFIG_DIR for this test
    local original_config_dir="$CONFIG_DIR"
    export CONFIG_DIR="$TEST_TEMP_DIR"
    
    local result=$(find_templates_dir)
    # The function now checks both templates and docs directories
    # Since we created engineering-workflow.md in docs, it should find that first
    assert_equals "$mock_docs" "$result"
    
    # Restore original CONFIG_DIR
    export CONFIG_DIR="$original_config_dir"
    

}

# Test find_install_script function
test_find_install_script_function() {
    test_start "find_install_script finds existing install script"
    
    # Create a mock install script
    local mock_install="$TEST_TEMP_DIR/install.sh"
    touch "$mock_install"
    chmod +x "$mock_install"
    
    # Create the expected directory structure
    mkdir -p "$TEST_TEMP_DIR/.local/ai-dev"
    cp "$mock_install" "$TEST_TEMP_DIR/.local/ai-dev/install.sh"
    
    # Override HOME for this test
    local original_home="$HOME"
    export HOME="$TEST_TEMP_DIR"
    
    local result=$(find_install_script)
    assert_equals "$TEST_TEMP_DIR/.local/ai-dev/install.sh" "$result"
    
    # Restore original HOME
    export HOME="$original_home"
    
    test_start "find_install_script returns error when no install script found"
    local original_home="$HOME"
    local original_pwd="$PWD"
    
    # Temporarily rename the real install.sh so it can't be found
    local real_install_backup="$TEST_TEMP_DIR/install_backup2"
    if [[ -f "install.sh" ]]; then
        mv install.sh "$real_install_backup"
    fi
    
    export HOME="/nonexistent/path"
    
    # Test the real function - it should now fail
    local result=0
    find_install_script >/dev/null 2>&1 || result=$?
    assert_equals "1" "$result"
    
    # Restore original state
    export HOME="$original_home"
    cd "$original_pwd"
    
    # Restore the real install.sh
    if [[ -f "$real_install_backup" ]]; then
        mv "$real_install_backup" install.sh
    fi
}

# Test profile resolution functions
test_profile_functions() {
    test_start "_load_env_once loads global env file when it exists"
    
    # Create a test global env file
    local test_global_env="$TEST_TEMP_DIR/.env"
    echo "TEST_GLOBAL_VAR=global_value" > "$test_global_env"
    
    local original_global_env="$GLOBAL_ENV_FILE"
    export GLOBAL_ENV_FILE="$test_global_env"
    
    _load_env_once
    assert_equals "global_value" "$TEST_GLOBAL_VAR"
    
    export GLOBAL_ENV_FILE="$original_global_env"
    unset TEST_GLOBAL_VAR
    
    test_start "_resolve_profile_cfg creates temp config with profile"
    
    # Create test profile
    mkdir -p "$AI_PROFILES_DIR"
    local test_profile="$AI_PROFILES_DIR/test.mcp.json"
    cat > "$test_profile" << 'EOF'
{
  "mcpServers": {
    "test": {
      "command": "test-command",
      "env": {
        "TEST_VAR": "${TEST_ENV_VAR:-default}"
      }
    }
  }
}
EOF
    
    export TEST_ENV_VAR="resolved_value"
    
    # Mock envsubst command
    mock_command "envsubst" 'sed "s/\${TEST_ENV_VAR:-default}/resolved_value/g"'
    
    local result=$(_resolve_profile_cfg "test")
    assert_file_exists "$result"
    assert_contains "$(cat "$result")" "resolved_value"
    
    restore_command "envsubst"
    unset TEST_ENV_VAR
    rm -f "$result"
}

# Run all test suites
main() {
    echo "Testing ai-utils.sh functions..."
    setup_test_env
    
    run_test_suite "Logging Functions" test_logging_functions
    run_test_suite "JQ Check Function" test_check_jq_function
    run_test_suite "Environment Validation" test_require_env_function
    run_test_suite "Environment Loading" test_load_env_from_file_function
    run_test_suite "Template Directory Finding" test_find_templates_dir_function
    run_test_suite "Install Script Finding" test_find_install_script_function
    run_test_suite "Profile Functions" test_profile_functions
    
    print_test_summary
}

# Run tests if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi