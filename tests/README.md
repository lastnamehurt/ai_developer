# AI Development Environment - Test Suite

Comprehensive test suite for the AI Development Environment scripts, providing unit and integration testing for all modular components.

## Overview

This test suite validates the functionality of the refactored AI development environment tools, ensuring reliability and maintainability of the modular bash script architecture.

### Test Structure

```
tests/
├── README.md                 # This documentation
├── run-tests.sh             # Main test runner
├── test-framework.sh        # Lightweight bash testing framework
├── test-ai-utils.sh         # Tests for ai-utils.sh utilities
├── test-ai-core.sh          # Tests for ai-core.sh environment functions
├── test-ai-project.sh       # Tests for ai-project.sh project management
└── test-ai-integration.sh   # End-to-end integration tests for main ai script
```

## Quick Start

### Running All Tests

```bash
# Run all tests with default settings
./tests/run-tests.sh

# Run with verbose output
./tests/run-tests.sh -v

# Run specific test suite
./tests/run-tests.sh utils

# Stop on first failure
./tests/run-tests.sh -f
```

### Running Individual Test Files

```bash
# Run specific test suite directly
./tests/test-ai-utils.sh
./tests/test-ai-core.sh
./tests/test-ai-project.sh
./tests/test-ai-integration.sh
```

## Test Coverage

### ai-utils.sh Tests (`test-ai-utils.sh`)

- **Logging Functions**: Tests all logging output (info, success, warning, error)
- **Environment Validation**: Tests `_require_env` function with various scenarios
- **Environment Loading**: Tests `load_env_from_file` with comments, quotes, invalid lines
- **Directory Finding**: Tests `find_templates_dir` and `find_install_script` functions
- **Profile Functions**: Tests `_resolve_profile_cfg` and `_load_env_once` functions
- **Utility Functions**: Tests `check_jq` function and dependency checking

**Key Test Scenarios:**
- ✅ Log functions produce correct output with emojis and colors
- ✅ Environment validation catches missing and empty variables
- ✅ Environment loading handles comments, quotes, and invalid syntax
- ✅ Directory finding handles missing paths gracefully
- ✅ Profile resolution with environment variable substitution

### ai-core.sh Tests (`test-ai-core.sh`)

- **Environment Loading**: Tests global and local environment file loading
- **Environment Checking**: Tests comprehensive environment status reporting
- **Tool Detection**: Tests detection of available AI tools (claude, cursor, etc.)
- **Profile Management**: Tests profile listing and current profile detection
- **Symlink Handling**: Tests detection of symlinked configuration files

**Key Test Scenarios:**
- ✅ Loads global environment with local overrides
- ✅ Reports missing files and directories correctly
- ✅ Detects available and unavailable tools
- ✅ Lists MCP profiles and shows current default
- ✅ Distinguishes between regular files and symlinks

### ai-project.sh Tests (`test-ai-project.sh`)

- **MCP Server File Creation**: Tests JSON generation for server configuration
- **Project Initialization**: Tests `.claude` and `.cursor` directory setup
- **Configuration Syncing**: Tests config synchronization between tools
- **Environment File Creation**: Tests `.env` template generation
- **Workflow Integration**: Tests engineering workflow file handling
- **Template Management**: Tests template directory discovery

**Key Test Scenarios:**
- ✅ Creates valid MCP server configuration JSON
- ✅ Sets up Claude and Cursor directories with proper symlinks
- ✅ Creates environment file templates with proper structure
- ✅ Handles missing templates gracefully
- ✅ Integrates workflow references into existing files

### ai (Main Script) Integration Tests (`test-ai-integration.sh`)

- **Command Routing**: Tests help, check, load, install, sync commands
- **Profile Management**: Tests profile-aware claude/cursor command execution
- **Argument Handling**: Tests argument parsing and preservation
- **Error Handling**: Tests graceful error handling and validation
- **Module Loading**: Tests successful sourcing of all modular components
- **Environment Requirements**: Tests required environment variable validation

**Key Test Scenarios:**
- ✅ All help commands show proper usage information
- ✅ Commands route to correct functions with proper arguments
- ✅ Profile validation catches invalid profiles
- ✅ Environment variable requirements enforced for specific profiles
- ✅ External command pass-through works correctly
- ✅ Modular architecture loads without errors

## Test Framework Features

The custom bash test framework (`test-framework.sh`) provides:

### Assertion Functions
- `assert_equals(expected, actual, message)` - String equality
- `assert_contains(haystack, needle, message)` - String contains
- `assert_not_contains(haystack, needle, message)` - String doesn't contain
- `assert_file_exists(file, message)` - File existence
- `assert_file_not_exists(file, message)` - File non-existence
- `assert_command_success(command, message)` - Command succeeds
- `assert_command_fails(command, message)` - Command fails

### Test Environment
- Isolated temporary directory for each test run
- Mock command capabilities for testing external dependencies
- Environment variable overrides for controlled testing
- Automatic cleanup on test completion or interruption

### Output Formats
- Concise dot notation for quick feedback
- Verbose mode with detailed test descriptions
- Color-coded results for easy visual parsing
- Test suite summaries with pass/fail counts

## Test Runner Options

### Command Line Arguments

```bash
./run-tests.sh [OPTIONS] [TEST_PATTERN]

Options:
  -v, --verbose         Show detailed test output
  -f, --fail-fast       Stop on first test failure  
  -c, --coverage        Show coverage information
  -h, --help            Show help message

Arguments:
  TEST_PATTERN         Run only tests matching pattern
```

### Environment Variables

```bash
VERBOSE=true          # Enable verbose output
FAIL_FAST=true        # Stop on first failure
COVERAGE=true         # Enable coverage reporting
```

### Usage Examples

```bash
# Standard test run
./run-tests.sh

# Verbose output with coverage
VERBOSE=true COVERAGE=true ./run-tests.sh

# Test only utility functions
./run-tests.sh utils

# Stop on first failure, verbose output
./run-tests.sh -v -f

# Test integration only
./run-tests.sh integration
```

## Test Development Guidelines

### Writing New Tests

1. **Follow naming convention**: `test_function_name_scenario()`
2. **Use descriptive test names**: Clearly describe what is being tested
3. **Test both success and failure cases**: Cover happy path and edge cases
4. **Clean up after tests**: Use `teardown_test_env()` or ensure temporary files are cleaned
5. **Mock external dependencies**: Use `mock_command()` for external tools

### Test Structure Template

```bash
test_your_function() {
    test_start "function_name does expected thing"
    
    # Setup test environment
    local test_file="$TEST_TEMP_DIR/test.txt"
    echo "test content" > "$test_file"
    
    # Execute function
    local result=$(your_function "$test_file")
    
    # Assert results
    assert_equals "expected_value" "$result"
    assert_file_exists "$test_file"
    
    test_start "function_name handles error case"
    
    # Test error scenario
    assert_command_fails "your_function /nonexistent/file"
}
```

### Best Practices

- **Test isolation**: Each test should be independent
- **Meaningful assertions**: Use descriptive error messages
- **Edge case coverage**: Test boundary conditions and error states
- **Performance consideration**: Keep tests fast and focused
- **Documentation**: Add comments for complex test scenarios

## Continuous Integration

### Running Tests in CI

```bash
#!/bin/bash
set -euo pipefail

# Install dependencies if needed
# ...

# Run tests with fail-fast and coverage
FAIL_FAST=true COVERAGE=true ./tests/run-tests.sh

# Exit with test results
```

### Prerequisites

- Bash 4.0+ (uses associative arrays and other modern features)
- POSIX utilities: `grep`, `sed`, `awk`, `sort`
- `jq` (for some integration tests, automatically installed if missing)

## Troubleshooting

### Common Issues

**Tests fail with "command not found"**
- Ensure all scripts in `bin/` are executable: `chmod +x bin/*`
- Verify PATH includes the test directory

**Permission denied errors**
- Check file permissions: `ls -la tests/`
- Make test files executable: `chmod +x tests/*.sh`

**Tests hang or timeout**
- Use verbose mode to identify hanging tests: `./run-tests.sh -v`
- Check for infinite loops in mocked commands

**Environment conflicts**
- Tests use isolated temporary directories
- If issues persist, check for global environment variable conflicts

### Debug Mode

```bash
# Run with bash debug output
bash -x ./tests/run-tests.sh -v

# Run specific test with debug
bash -x ./tests/test-ai-utils.sh
```

## Contributing

When adding new functionality to the AI development environment:

1. **Add corresponding tests** for new functions
2. **Update existing tests** if function behavior changes  
3. **Run full test suite** before submitting changes
4. **Add integration tests** for new commands or workflows
5. **Update test documentation** for significant changes

### Test-Driven Development

1. Write failing tests for new functionality
2. Implement the minimum code to make tests pass
3. Refactor while keeping tests green
4. Add edge case tests and improve error handling

## Support

For issues with the test suite:

1. Check this README for troubleshooting steps
2. Run tests in verbose mode for detailed output
3. Examine individual test files for specific test logic
4. Review the test framework code for assertion behavior

The test suite is designed to be self-documenting through clear test names and comprehensive coverage of all functionality.