#!/usr/bin/env bash

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Installation directory
INSTALL_DIR="$HOME/.local/aidev"
BIN_DIR="$INSTALL_DIR/bin"
# Remote source for installs when not running inside the repo
REPO_URL="${AIDEV_REPO_URL:-https://github.com/lastnamehurt/aidev.git}"
PACKAGE_SOURCE="${AIDEV_INSTALL_SOURCE:-aidev}"
# Preferred installer (pipx isolates deps, no venv activation needed)
USE_PIPX="${AIDEV_USE_PIPX:-1}"
PIPX_BIN_DIR="$HOME/.local/bin"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  aidev Installation${NC}"
echo -e "${CYAN}========================================${NC}"
echo

# Check Python version
echo -e "${CYAN}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.10 or later"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if ! python3 -c "import sys; sys.exit(0 if tuple(map(int, '$PYTHON_VERSION'.split('.'))) >= tuple(map(int, '$REQUIRED_VERSION'.split('.'))) else 1)"; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or later is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install_with_pipx() {
    if ! command -v pipx >/dev/null 2>&1; then
        echo -e "${YELLOW}! pipx not found; attempting to install via pip --user${NC}"
        python3 -m pip install --user pipx || return 1
        export PATH="$HOME/.local/bin:$PATH"
    fi
    echo -e "${CYAN}Installing via pipx...${NC}"
    if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
        pipx install --force "$SCRIPT_DIR" && return 0
    fi
    pipx install --force "$PACKAGE_SOURCE" && return 0
    echo -e "${YELLOW}!${NC} pipx install from package failed, trying git..."
    pipx install --force "git+$REPO_URL"
}

install_with_venv() {
    echo
    echo -e "${CYAN}Creating virtual environment...${NC}"
    if [ ! -d "$INSTALL_DIR/venv" ]; then
        python3 -m venv "$INSTALL_DIR/venv"
        echo -e "${GREEN}✓${NC} Virtual environment created"
    else
        echo -e "${YELLOW}Virtual environment already exists${NC}"
    fi
    source "$INSTALL_DIR/venv/bin/activate"
    echo
    echo -e "${CYAN}Upgrading pip...${NC}"
    pip install --quiet --upgrade pip
    echo
    echo -e "${CYAN}Installing aidev...${NC}"
    if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
        pip install --quiet -e "$SCRIPT_DIR"
        echo -e "${GREEN}✓${NC} Installed aidev from source (development mode)"
    else
        if pip install --quiet "$PACKAGE_SOURCE"; then
            echo -e "${GREEN}✓${NC} Installed aidev from package source: $PACKAGE_SOURCE"
        else
            echo -e "${YELLOW}!${NC} Primary install source failed, trying git repository..."
            if pip install --quiet "git+$REPO_URL"; then
                echo -e "${GREEN}✓${NC} Installed aidev from git: $REPO_URL"
            else
                echo -e "${RED}Error: Failed to install aidev from both $PACKAGE_SOURCE and $REPO_URL${NC}"
                exit 1
            fi
        fi
    fi
}

# Install aidev (prefer pipx to avoid venv activation)
if [ "$USE_PIPX" = "1" ]; then
    install_with_pipx || install_with_venv

    # Clean up legacy venv-based installation if it exists
    if [ -d "$INSTALL_DIR/venv" ]; then
        echo
        echo -e "${YELLOW}! Found legacy venv installation at $INSTALL_DIR${NC}"
        read -p "Remove legacy installation? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"
            echo -e "${GREEN}✓${NC} Removed legacy installation"
        fi
    fi
else
    install_with_venv
fi

# Create bin directory and wrapper script
echo
echo -e "${CYAN}Creating launcher script...${NC}"
mkdir -p "$BIN_DIR"

if [ "$USE_PIPX" = "1" ]; then
    echo
    echo -e "${CYAN}pipx handles launchers (ai/aidev on PATH if pipx bin is in PATH).${NC}"
    echo -e "${YELLOW}!${NC} Ensuring pipx bin dir is in PATH (typically $PIPX_BIN_DIR)"
    if [[ ":$PATH:" != *":$PIPX_BIN_DIR:"* ]]; then
        # Prepend for current session
        export PATH="$PIPX_BIN_DIR:$PATH"
        # Optionally append to shell rc
        if [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        elif [ -n "$BASH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
        fi
        if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
            # Check if PATH entry already exists (avoid duplicates)
            if ! grep -qF "$PIPX_BIN_DIR" "$SHELL_RC"; then
                echo "export PATH=\"$PIPX_BIN_DIR:\$PATH\"" >> "$SHELL_RC"
                echo -e "${GREEN}✓${NC} Added $PIPX_BIN_DIR to $SHELL_RC"
            else
                echo -e "${GREEN}✓${NC} $PIPX_BIN_DIR already in $SHELL_RC"
            fi
        fi
    fi
else
    echo
    echo -e "${CYAN}Creating launcher script...${NC}"
    mkdir -p "$BIN_DIR"

    cat > "$BIN_DIR/aidev" << 'EOFBIN'
#!/usr/bin/env bash
# aidev launcher script

INSTALL_DIR="$HOME/.local/aidev"
source "$INSTALL_DIR/venv/bin/activate"
exec python -m aidev.cli "$@"
EOFBIN

    chmod +x "$BIN_DIR/aidev"

    # Create shorter 'ai' alias
    cat > "$BIN_DIR/ai" << 'EOFBIN'
#!/usr/bin/env bash
# ai launcher script (alias for aidev)

INSTALL_DIR="$HOME/.local/aidev"
source "$INSTALL_DIR/venv/bin/activate"
exec python -m aidev.cli "$@"
EOFBIN

    chmod +x "$BIN_DIR/ai"
    echo -e \"${GREEN}✓${NC} Created launchers: $BIN_DIR/aidev and $BIN_DIR/ai\"
fi

if [ "$USE_PIPX" != "1" ]; then
    echo
    echo -e "${CYAN}Checking PATH configuration...${NC}"

    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        echo -e "${YELLOW}! $BIN_DIR is not in your PATH${NC}"
        echo
        echo \"Add the following line to your shell configuration file:\"
        echo

        # Detect shell
        if [ -n "$ZSH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
            echo -e "${CYAN}  echo 'export PATH=\"\$HOME/.local/aidev/bin:\$PATH\"' >> ~/.zshrc${NC}"
        elif [ -n "$BASH_VERSION" ]; then
            SHELL_RC="$HOME/.zshrc"
            echo -e "${CYAN}  echo 'export PATH=\"\$HOME/.local/aidev/bin:\$PATH\"' >> ~/.zshrc${NC}"
        else
            echo -e "${CYAN}  export PATH=\"\$HOME/.local/aidev/bin:\$PATH\"${NC}"
        fi

        echo
        echo \"Then run:\"
        echo -e \"${CYAN}  source $SHELL_RC${NC}\"
        echo

        # Offer to add automatically
        read -p "Add to PATH automatically? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if [ -n "$SHELL_RC" ] && [ -f "$SHELL_RC" ]; then
                # Check if PATH entry already exists (avoid duplicates)
                if ! grep -qF "\$HOME/.local/aidev/bin" "$SHELL_RC"; then
                    echo "export PATH=\"\$HOME/.local/aidev/bin:\$PATH\"" >> "$SHELL_RC"
                    echo -e "${GREEN}✓${NC} Added to $SHELL_RC"
                    echo -e "${YELLOW}! Run: source $SHELL_RC${NC}"
                else
                    echo -e "${GREEN}✓${NC} PATH already contains \$HOME/.local/aidev/bin in $SHELL_RC"
                fi
            fi
        fi
    else
        echo -e \"${GREEN}✓${NC} $BIN_DIR is in PATH\"
    fi
fi

# Initialize aidev
echo
echo -e "${CYAN}Initializing aidev...${NC}"
"$BIN_DIR/aidev" setup --force > /dev/null 2>&1 || true
echo -e "${GREEN}✓${NC} aidev initialized"

# Prepare Gemini CLI config directory (for MCP settings)
GEMINI_DIR="$HOME/.gemini"
GEMINI_SETTINGS="$GEMINI_DIR/settings.json"
mkdir -p "$GEMINI_DIR"
if [ ! -f "$GEMINI_SETTINGS" ]; then
    echo '{ "mcpServers": {} }' > "$GEMINI_SETTINGS"
    echo -e "${GREEN}✓${NC} Created $GEMINI_SETTINGS"
else
    echo -e "${GREEN}✓${NC} Gemini settings detected at $GEMINI_SETTINGS"
fi

# Install git MCP server (Go)
echo
echo -e "${CYAN}Installing git MCP server...${NC}"
if command -v go >/dev/null 2>&1; then
    GOPATH="${GOPATH:-$(go env GOPATH)}"
    GOBIN="${GOBIN:-$GOPATH/bin}"
    go install github.com/geropl/git-mcp-go@latest >/dev/null 2>&1 && \
      echo -e "${GREEN}✓${NC} git-mcp-go installed to ${GOBIN:-$GOPATH/bin}" || \
      echo -e "${YELLOW}!${NC} git-mcp-go installation failed (ensure Go is set up)"
else
    echo -e "${YELLOW}!${NC} Go not found; skipping git-mcp-go install"
fi

# Summary
echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo "Next steps:"
echo "  1. Ensure $BIN_DIR is in your PATH"
echo "  2. Run: ai doctor (or aidev doctor)"
echo "  3. Configure: ai setup"
echo "  4. In a project: ai init"
echo "  5. Launch a tool: ai cursor"
echo
echo "Documentation: $SCRIPT_DIR/README.md"
echo

# Test installation
if command -v ai &> /dev/null; then
    echo -e "${GREEN}✓${NC} ai/aidev commands are available"
    ai --version
else
    echo -e "${YELLOW}! ai command not found in current shell${NC}"
    echo -e "${YELLOW}  Add to PATH and restart your shell${NC}"
fi
