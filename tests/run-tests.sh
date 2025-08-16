#!/bin/bash

# Test Runner for AI Development Environment
# Runs all test suites and provides comprehensive reporting

set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Test configuration
VERBOSE=${VERBOSE:-false}
FAIL_FAST=${FAIL_FAST:-false}
FILTER=${FILTER:-""}
COVERAGE=${COVERAGE:-false}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Test results tracking
TOTAL_TESTS=0
TOTAL_PASSED=0
TOTAL_FAILED=0
FAILED_SUITES=()

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo -e "${BOLD}${BLUE}$1${NC}"
}

show_usage() {
    cat << EOF
Test Runner for AI Development Environment

Usage: $0 [OPTIONS] [TEST_PATTERN]

Options:
  -v, --verbose         Show detailed test output
  -f, --fail-fast       Stop on first test failure
  -c, --coverage        Show coverage information (if available)
  -h, --help            Show this help message
  
Arguments:
  TEST_PATTERN         Run only tests matching this pattern (e.g., "utils", "core")

Environment Variables:
  VERBOSE=true          Enable verbose output
  FAIL_FAST=true        Stop on first failure
  COVERAGE=true         Enable coverage reporting

Examples:
  $0                    # Run all tests
  $0 -v                 # Run all tests with verbose output
  $0 utils              # Run only ai-utils tests
  $0 -f integration     # Run integration tests, stop on first failure
  $0 installation       # Run only installation tests
  $0 profiles           # Run only profile system tests
  $0 agents             # Run only sub agents tests
  VERBOSE=true $0       # Run with verbose output via environment
EOF
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -f|--fail-fast)
                FAIL_FAST=true
                shift
                ;;
            -c|--coverage)
                COVERAGE=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            -*|--*)
                log_error "Unknown option $1"
                show_usage
                exit 1
                ;;
            *)
                FILTER="$1"
                shift
                ;;
        esac
    done
}

check_dependencies() {
    local missing_deps=()
    
    # Check for bash
    if ! command -v bash >/dev/null 2>&1; then
        missing_deps+=("bash")
    fi
    
    # Check for basic POSIX utilities
    for cmd in grep sed awk sort; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Missing required dependencies: ${missing_deps[*]}"
        exit 1
    fi
}

validate_test_environment() {
    log_info "Validating test environment..."
    
    # Check that source files exist
    local bin_dir="$PROJECT_ROOT/bin"
    local required_files=(
        "$bin_dir/ai"
        "$bin_dir/ai-utils.sh" 
        "$bin_dir/ai-core.sh"
        "$bin_dir/ai-project.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Required file not found: $file"
            exit 1
        fi
        
        if [[ ! -x "$file" ]]; then
            log_warning "File not executable: $file"
            chmod +x "$file" 2>/dev/null || log_error "Cannot make executable: $file"
        fi
    done
    
    # Check test files exist and are executable
    local test_files=(
        "$SCRIPT_DIR/test-ai-utils.sh"
        "$SCRIPT_DIR/test-ai-core.sh"
        "$SCRIPT_DIR/test-ai-project.sh"
        "$SCRIPT_DIR/test-ai-integration.sh"
        "$SCRIPT_DIR/test-ai-installation.sh"
        "$SCRIPT_DIR/test-ai-profiles.sh"
        "$SCRIPT_DIR/test-ai-agents.sh"
    )
    
    for file in "${test_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            log_error "Test file not found: $file"
            exit 1
        fi
        
        if [[ ! -x "$file" ]]; then
            chmod +x "$file" 2>/dev/null || log_error "Cannot make test file executable: $file"
        fi
    done
    
    log_success "Test environment validated"
}

run_test_suite() {
    local test_file="$1"
    local suite_name="$2"
    
    # Apply filter if specified
    if [[ -n "$FILTER" && "$suite_name" != *"$FILTER"* ]]; then
        if [[ "$VERBOSE" == "true" ]]; then
            log_info "Skipping $suite_name (filtered out)"
        fi
        return 0
    fi
    
    log_header "Running $suite_name"
    echo "======================================="
    
    local start_time=$(date +%s)
    local result=0
    local output
    
    if [[ "$VERBOSE" == "true" ]]; then
        export VERBOSE=true
        "$test_file" || result=$?
    else
        export VERBOSE=false
        output=$("$test_file" 2>&1) || result=$?
        
        # Parse test results from output
        local passed failed
        # Look for success pattern: "✅ suite_name: X passed"
        passed=$(echo "$output" | grep -o "✅.*: [0-9]\+ passed" | head -1 | grep -o "[0-9]\+" || echo "0")
        # Look for failure pattern: "❌ suite_name: X passed, Y failed"
        failed=$(echo "$output" | grep -o "❌.*: [0-9]\+ passed, [0-9]\+ failed" | head -1 | grep -o "[0-9]\+ failed" | grep -o "[0-9]\+" || echo "0")
        
        # Ensure variables are numeric for arithmetic operations
        passed=${passed:-0}
        failed=${failed:-0}
        
        TOTAL_PASSED=$((TOTAL_PASSED + passed))
        TOTAL_FAILED=$((TOTAL_FAILED + failed))
        TOTAL_TESTS=$((TOTAL_TESTS + passed + failed))
        
        if [[ $result -eq 0 ]]; then
            log_success "$suite_name: $passed tests passed"
        else
            log_error "$suite_name: $failed tests failed"
            FAILED_SUITES+=("$suite_name")
            
            if [[ "$VERBOSE" == "false" ]]; then
                echo "Failure details:"
                echo "$output" | grep -E "(❌|FAIL)" || true
            fi
        fi
    fi
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [[ "$VERBOSE" == "true" ]]; then
        echo "Duration: ${duration}s"
    fi
    echo
    
    # Stop on failure if fail-fast is enabled
    if [[ $result -ne 0 && "$FAIL_FAST" == "true" ]]; then
        log_error "Stopping due to test failure (--fail-fast enabled)"
        exit 1
    fi
    
    return $result
}

show_coverage_info() {
    if [[ "$COVERAGE" != "true" ]]; then
        return 0
    fi
    
    log_header "Test Coverage Analysis"
    echo "======================================="
    
    local bin_dir="$PROJECT_ROOT/bin"
    
    log_info "Analyzing function coverage..."
    
    # Extract function definitions from source files
    echo "Functions in ai-utils.sh:"
    grep -n "^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*(" "$bin_dir/ai-utils.sh" | head -10 || true
    
    echo
    echo "Functions in ai-core.sh:"
    grep -n "^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*(" "$bin_dir/ai-core.sh" | head -10 || true
    
    echo
    echo "Functions in ai-project.sh:"
    grep -n "^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*(" "$bin_dir/ai-project.sh" | head -10 || true
    
    echo
    log_info "Coverage analysis complete"
    log_warning "Note: Detailed coverage requires additional tooling"
    echo
}

print_final_summary() {
    echo
    log_header "Final Test Results"
    echo "========================================="
    
    local total_suites=7
    local passed_suites=$((total_suites - ${#FAILED_SUITES[@]}))
    
    echo "Test Suites: $passed_suites/$total_suites passed"
    
    if [[ "$VERBOSE" != "true" && $TOTAL_TESTS -gt 0 ]]; then
        echo "Total Tests: $TOTAL_TESTS"
        echo "Passed: $TOTAL_PASSED"
        echo "Failed: $TOTAL_FAILED"
        echo "Success Rate: $(( (TOTAL_PASSED * 100) / TOTAL_TESTS ))%"
    fi
    
    if [[ ${#FAILED_SUITES[@]} -gt 0 ]]; then
        echo
        log_error "Failed test suites:"
        for suite in "${FAILED_SUITES[@]}"; do
            echo "  - $suite"
        done
        echo
        log_error "Some tests failed"
        exit 1
    else
        echo
        log_success "🎉 All tests passed!"
        exit 0
    fi
}

run_all_tests() {
    local start_time=$(date +%s)
    
    log_header "AI Development Environment Test Suite"
    echo "======================================="
    echo "Project: $(basename "$PROJECT_ROOT")"
    echo "Test Directory: $SCRIPT_DIR"
    echo "Verbose: $VERBOSE"
    echo "Fail Fast: $FAIL_FAST"
    echo "Filter: ${FILTER:-"(none)"}"
    echo "Coverage: $COVERAGE"
    echo
    
    # Run test suites
    run_test_suite "$SCRIPT_DIR/test-ai-utils.sh" "AI Utils Tests"
    run_test_suite "$SCRIPT_DIR/test-ai-core.sh" "AI Core Tests" 
    run_test_suite "$SCRIPT_DIR/test-ai-project.sh" "AI Project Tests"
    run_test_suite "$SCRIPT_DIR/test-ai-integration.sh" "AI Integration Tests"
    run_test_suite "$SCRIPT_DIR/test-ai-installation.sh" "Installation Tests"
    run_test_suite "$SCRIPT_DIR/test-ai-profiles.sh" "Profile System Tests"
    run_test_suite "$SCRIPT_DIR/test-ai-agents.sh" "Sub Agents Tests"
    
    # Show coverage if requested
    show_coverage_info
    
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    
    echo "Total test execution time: ${total_duration}s"
    
    print_final_summary
}

main() {
    parse_arguments "$@"
    check_dependencies
    validate_test_environment
    run_all_tests
}

# Handle signals for cleanup
trap 'log_error "Test run interrupted"; exit 130' INT TERM

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi