# Test Overlap Analyzer MCP Server

A Model Context Protocol (MCP) server that analyzes RSpec tests to find overlapping coverage between smoke-tagged E2E tests and unit/integration tests.

## Features

- **Smoke Test Detection**: Identifies E2E tests tagged with "smoke" using various RSpec patterns
- **Overlap Analysis**: Finds redundant tests between E2E and unit/integration test suites
- **Environment Configuration**: Uses environment variables for easy configuration
- **Simple Interface**: Two main tools: analyze and show configuration

## Installation

```bash
npm install
```

## Usage

### Environment Variables

Set these environment variables to configure the analyzer:

```bash
# Required
export E2E_REPO_PATH="/path/to/e2e-tests"
export MONOLITH_REPO_PATH="/path/to/monolith-tests"

# Optional (with defaults)
export E2E_SUB_PATH="spec/features"        # default
export MONOLITH_SUB_PATH="spec"            # default  
export SMOKE_TAG_PATTERN="smoke"          # default
```

### Running the Server

```bash
npm start
```

Or directly:

```bash
npx tsx index.ts
```

## Available Tools

### `analyze_test_overlap`

Analyzes overlap between smoke-tagged E2E tests and unit tests.

**Input**: None (uses environment variables)

**Output**: JSON analysis result with:
- Total E2E and unit test counts
- Overlap analysis with redundancy scores
- Recommendations (remove/refactor/keep)
- Estimated time savings

### `show_config`

Shows current configuration and available environment variables.

**Input**: None

**Output**: Current configuration and environment variable documentation

## Example

```bash
# Set up environment
export E2E_REPO_PATH="/Users/me/projects/e2e-tests"
export MONOLITH_REPO_PATH="/Users/me/projects/monolith"

# Run analysis
npm start
```

The server will:
1. Scan the E2E repo for smoke-tagged tests
2. Scan the monolith repo for unit/integration tests  
3. Analyze overlaps and provide recommendations
4. Return detailed JSON results

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `E2E_REPO_PATH` | Yes | - | Path to E2E test repository |
| `MONOLITH_REPO_PATH` | Yes | - | Path to monolith repository |
| `E2E_SUB_PATH` | No | `spec/features` | Subdirectory in E2E repo |
| `MONOLITH_SUB_PATH` | No | `spec` | Subdirectory in monolith repo |
| `SMOKE_TAG_PATTERN` | No | `smoke` | Pattern to identify smoke tests | 