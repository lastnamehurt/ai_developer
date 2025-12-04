# Contributing to aidev

Thank you for your interest in contributing to aidev! This guide will help you get started.

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/aidev.git
cd aidev
```

2. Install in development mode:
```bash
./install.sh
```

3. Install development dependencies:
```bash
source ~/.local/aidev/venv/bin/activate
pip install -e ".[dev]"
```

## Code Style

We follow standard Python conventions:

- **Formatting**: Black (line length: 100)
- **Linting**: Ruff
- **Type hints**: Required for all public functions
- **Docstrings**: Google style

Run code quality checks:

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## Testing

We use pytest for testing. Write tests for all new features:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=aidev --cov-report=html

# Run specific test file
pytest tests/unit/test_profiles.py

# Run specific test
pytest tests/unit/test_profiles.py::TestProfileManager::test_create_profile
```

### Test Organization

- `tests/unit/` - Unit tests (fast, isolated)
- `tests/integration/` - Integration tests (slower, may require setup)

## Making Changes

1. Create a feature branch:
```bash
git checkout -b feature/my-feature
```

2. Make your changes:
   - Write code following the style guide
   - Add tests for new functionality
   - Update documentation if needed

3. Run tests and quality checks:
```bash
pytest
black src/ tests/
ruff check src/ tests/
mypy src/
```

4. Commit your changes:
```bash
git add .
git commit -m "Add feature: description of feature"
```

5. Push and create a pull request:
```bash
git push origin feature/my-feature
```

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the documentation in `docs/` if needed
3. Add tests for new features
4. Ensure all tests pass
5. Update the version in `pyproject.toml` following SemVer
6. The PR will be merged once you have approval

## Adding New MCP Servers

To add a new built-in MCP server:

1. Add configuration to `src/aidev/mcp.py` in `_get_builtin_servers()`
2. Add to appropriate built-in profiles in `src/aidev/profiles.py`
3. Add documentation in README.md
4. Add tests

Example:

```python
def _get_builtin_servers(self) -> dict[str, dict]:
    return {
        # ... existing servers ...
        "my-server": {
            "name": "my-server",
            "description": "My custom MCP server",
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@myorg/mcp-server-my-server"],
            "env": {
                "MY_API_KEY": "${MY_API_KEY}",
            },
        },
    }
```

## Adding New Profiles

To add a new built-in profile:

1. Add to `src/aidev/profiles.py` in `_get_builtin_profiles()`
2. Add to `BUILTIN_PROFILES` in `src/aidev/constants.py`
3. Document in README.md

Example:

```python
Profile(
    name="my-profile",
    description="My custom profile for X workflow",
    mcp_servers=[
        MCPServerConfig(name="filesystem", enabled=True),
        MCPServerConfig(name="git", enabled=True),
        MCPServerConfig(name="my-server", enabled=True),
    ],
    environment={
        "MY_API_KEY": "${MY_API_KEY}",
    },
)
```

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions (Google style)
- Update docs/ for architecture or design changes

## Reporting Issues

When reporting issues, please include:

- aidev version (`aidev --version`)
- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages (if any)

## Feature Requests

Feature requests are welcome! Please:

1. Check if the feature already exists
2. Describe the use case
3. Explain why this would be useful
4. Suggest a possible implementation (optional)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Questions?

Feel free to open an issue for:
- Questions about the codebase
- Clarification on features
- Discussion about proposed changes

Thank you for contributing to aidev!
