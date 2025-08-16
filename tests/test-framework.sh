#!/bin/bash

# Bash Test Framework for AI Development Environment
# Simple, lightweight testing framework for bash scripts

set -euo pipefail

# Test framework variables
TESTS_PASSED=0
TESTS_FAILED=0
CURRENT_TEST=""
TEST_OUTPUT=""
VERBOSE=${VERBOSE:-false}

# Colors for test output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test framework functions
test_start() {
    local test_name="$1"
    CURRENT_TEST="$test_name"
    TEST_OUTPUT=""
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}Running: $test_name${NC}"
    fi
}

test_pass() {
    ((TESTS_PASSED++))
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${GREEN}✅ PASS: $CURRENT_TEST${NC}"
    else
        echo -n "."
    fi
}

test_fail() {
    local message="${1:-Test failed}"
    ((TESTS_FAILED++))
    echo -e "${RED}❌ FAIL: $CURRENT_TEST${NC}"
    echo -e "${RED}   $message${NC}"
    if [[ -n "$TEST_OUTPUT" ]]; then
        echo -e "${YELLOW}   Output: $TEST_OUTPUT${NC}"
    fi
}

# Assertion functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-Expected '$expected', got '$actual'}"
    
    if [[ "$expected" == "$actual" ]]; then
        test_pass
    else
        test_fail "$message"
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-Expected '$haystack' to contain '$needle'}"
    
    if [[ "$haystack" == *"$needle"* ]]; then
        test_pass
    else
        test_fail "$message"
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-Expected '$haystack' to not contain '$needle'}"
    
    if [[ "$haystack" != *"$needle"* ]]; then
        test_pass
    else
        test_fail "$message"
    fi
}

assert_file_exists() {
    local file="$1"
    local message="${2:-Expected file '$file' to exist}"
    
    if [[ -f "$file" ]]; then
        test_pass
    else
        test_fail "$message"
    fi
}

assert_file_not_exists() {
    local file="$1"
    local message="${2:-Expected file '$file' to not exist}"
    
    if [[ ! -f "$file" ]]; then
        test_pass
    else
        test_fail "$message"
    fi
}

assert_command_success() {
    local command="$1"
    local message="${2:-Command '$command' should succeed}"
    
    if eval "$command" >/dev/null 2>&1; then
        test_pass
    else
        test_fail "$message"
    fi
}

assert_command_fails() {
    local command="$1"
    local message="${2:-Command '$command' should fail}"
    
    if ! eval "$command" >/dev/null 2>&1; then
        test_pass
    else
        test_fail "$message"
    fi
}

capture_output() {
    local command="$1"
    TEST_OUTPUT=$(eval "$command" 2>&1 || true)
    echo "$TEST_OUTPUT"
}

# Test suite functions
run_test_suite() {
    local suite_name="$1"
    local test_function="$2"
    
    echo -e "${BLUE}Running test suite: $suite_name${NC}"
    
    # Reset counters for this suite
    local suite_passed=0
    local suite_failed=0
    local original_passed=$TESTS_PASSED
    local original_failed=$TESTS_FAILED
    
    # Run the test function
    $test_function
    
    # Calculate suite results
    suite_passed=$((TESTS_PASSED - original_passed))
    suite_failed=$((TESTS_FAILED - original_failed))
    
    # Print suite summary
    if [[ $suite_failed -eq 0 ]]; then
        echo -e "${GREEN}✅ $suite_name: $suite_passed passed${NC}"
    else
        echo -e "${RED}❌ $suite_name: $suite_passed passed, $suite_failed failed${NC}"
    fi
    echo
}

# Test results summary
print_test_summary() {
    local total=$((TESTS_PASSED + TESTS_FAILED))
    
    echo "========================================="
    echo "Test Results Summary"
    echo "========================================="
    echo "Total tests: $total"
    echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}🎉 All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}💥 Some tests failed${NC}"
        exit 1
    fi
}

# Setup and teardown functions
setup_test_env() {
    # Create temporary directory for tests
    export TEST_TEMP_DIR=$(mktemp -d)
    export ORIGINAL_PWD=$(pwd)
    
    # Set up fake environment variables for testing
    export TEST_CONFIG_DIR="$TEST_TEMP_DIR/.test-ai-dev"
    export TEST_BIN_DIR="$TEST_CONFIG_DIR/bin"
    export TEST_ENV_FILE="$TEST_CONFIG_DIR/.env"
    
    mkdir -p "$TEST_CONFIG_DIR"
    mkdir -p "$TEST_BIN_DIR"
    
    # Override global variables for testing
    export CONFIG_DIR="$TEST_CONFIG_DIR"
    export GLOBAL_ENV_FILE="$TEST_ENV_FILE"
    export ENV_FILE=".env"
    export MCP_FILE=".mcp.json"
    export AI_PROFILES_DIR="$TEST_CONFIG_DIR/mcp-profiles"
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Test environment created at: $TEST_TEMP_DIR"
    fi
}

teardown_test_env() {
    if [[ -n "${TEST_TEMP_DIR:-}" && -d "$TEST_TEMP_DIR" ]]; then
        rm -rf "$TEST_TEMP_DIR"
    fi
    
    if [[ -n "${ORIGINAL_PWD:-}" ]]; then
        cd "$ORIGINAL_PWD"
    fi
}

# Utility functions for testing
mock_command() {
    local command_name="$1"
    local mock_script="$2"
    
    # Create a mock executable in a temp bin directory
    local mock_bin="$TEST_TEMP_DIR/mock_bin"
    mkdir -p "$mock_bin"
    
    cat > "$mock_bin/$command_name" << EOF
#!/bin/bash
$mock_script
EOF
    chmod +x "$mock_bin/$command_name"
    
    # Add to PATH for this test
    export PATH="$mock_bin:$PATH"
}

restore_command() {
    local command_name="$1"
    
    # Remove mock from PATH
    if [[ -f "$TEST_TEMP_DIR/mock_bin/$command_name" ]]; then
        rm -f "$TEST_TEMP_DIR/mock_bin/$command_name"
        # Remove the mock bin directory from PATH if it's empty
        if [[ -z "$(ls -A "$TEST_TEMP_DIR/mock_bin" 2>/dev/null)" ]]; then
            export PATH=$(echo "$PATH" | sed "s|$TEST_TEMP_DIR/mock_bin:||")
        fi
    fi
}

# Signal handlers for cleanup
trap 'teardown_test_env' EXIT INT TERM