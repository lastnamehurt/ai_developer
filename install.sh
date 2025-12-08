#!/usr/bin/env bash

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Installation directory (legacy venv fallback)
INSTALL_DIR="$HOME/.local/aidev"
BIN_DIR="$INSTALL_DIR/bin"
# Remote source for installs when not running inside the repo
REPO_URL="${AIDEV_REPO_URL:-https://github.com/lastnamehurt/aidev.git}"
PACKAGE_SOURCE="${AIDEV_INSTALL_SOURCE:-aidev}"
# Preferred installer (pipx isolates deps, no venv activation needed)
USE_PIPX="${AIDEV_USE_PIPX:-1}"

# Detect pipx bin dir (fallback to ~/.local/bin)
detect_pipx_bin_dir() {
    if command -v pipx >/dev/null 2>&1; then
        # pipx environment --value PIPX_BIN_DIR available in recent pipx
        local detected
        detected=$(pipx environment --value PIPX_BIN_DIR 2>/dev/null || true)
        if [ -n "$detected" ]; then
            echo "$detected"
            return
        fi
        # Older pipx prints lines; parse
        detected=$(pipx environment 2>/dev/null | sed -n 's/^PIPX_BIN_DIR=//p' | head -n1)
        if [ -n "$detected" ]; then
            echo "$detected"
            return
        fi
    fi
    echo "$HOME/.local/bin"
}

PIPX_BIN_DIR="${PIPX_BIN_DIR:-$(detect_pipx_bin_dir)}"
HOMEBREW_BIN_DIR="/opt/homebrew/bin"

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

ensure_path_entry() {
    local dir="$1"
    local label="$2"
    if [ -z "$dir" ]; then
        return
    fi
    if [[ ":$PATH:" != *":$dir:"* ]]; then
        export PATH="$dir:$PATH"
        local shell_rc=""
        if [ -n "$ZSH_VERSION" ]; then
            shell_rc="$HOME/.zshrc"
        elif [ -n "$BASH_VERSION" ]; then
            shell_rc="$HOME/.zshrc"
        fi
        if [ -n "$shell_rc" ] && [ -f "$shell_rc" ] && ! grep -qF "$dir" "$shell_rc"; then
            echo "export PATH=\"$dir:\$PATH\"" >> "$shell_rc"
            echo -e "${GREEN}✓${NC} Added $dir to $shell_rc ($label)"
        elif [ -n "$shell_rc" ] && [ -f "$shell_rc" ]; then
            echo -e "${GREEN}✓${NC} $label already in PATH via $shell_rc"
        fi
    fi
}

install_with_pipx() {
    if ! command -v pipx >/dev/null 2>&1; then
        echo -e "${YELLOW}! pipx not found; attempting to install via pip --user${NC}"
        python3 -m pip install --user pipx || return 1
        pipx ensurepath >/dev/null 2>&1 || true
        PIPX_BIN_DIR="$(detect_pipx_bin_dir)"
        ensure_path_entry "$PIPX_BIN_DIR" "pipx bin"
    fi
    # Ensure pipx shims are on PATH (helps current shell)
    pipx ensurepath >/dev/null 2>&1 || true
    PIPX_BIN_DIR="$(detect_pipx_bin_dir)"
    ensure_path_entry "$PIPX_BIN_DIR" "pipx bin"
    ensure_path_entry "$HOMEBREW_BIN_DIR" "Homebrew bin"

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
    ensure_path_entry "$PIPX_BIN_DIR" "pipx bin"
    ensure_path_entry "$HOMEBREW_BIN_DIR" "Homebrew bin"
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
AIDEV_BIN="$(command -v ai || command -v aidev || true)"
if [ -z "$AIDEV_BIN" ]; then
    echo -e "${YELLOW}! Could not find ai/aidev on PATH in this shell. Open a new shell or run: pipx ensurepath && hash -r${NC}"
else
    "$AIDEV_BIN" setup --force > /dev/null 2>&1 || true
fi
echo -e "${GREEN}✓${NC} aidev initialized"

# Detect conflicting ai binaries (e.g., local venv shadowing pipx)
if command -v ai >/dev/null 2>&1; then
    PRIMARY_AI="$(command -v ai)"
    ALL_AI="$(which -a ai 2>/dev/null | tr '\n' ' ')"
    echo -e "${CYAN}ai resolution:${NC} $PRIMARY_AI"
    if echo "$PRIMARY_AI" | grep -E "/venv/|/.venv/" >/dev/null 2>&1; then
        echo -e "${YELLOW}! Current ai points to a virtualenv ($PRIMARY_AI). pipx shim may be shadowed.${NC}"
    elif [ -n "$PIPX_BIN_DIR" ] && [[ "$PRIMARY_AI" != "$PIPX_BIN_DIR/"* ]]; then
        echo -e "${YELLOW}! Current ai is not from pipx. Consider: pipx reinstall ai-developer --force${NC}"
    fi
    if [ -n "$ALL_AI" ]; then
        echo -e "${CYAN}All ai locations:${NC} $ALL_AI"
    fi
fi

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

# Install GitHub CLI (gh)
echo
echo -e "${CYAN}Installing GitHub CLI (gh)...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}! Homebrew not found; skipping gh install. Please install Homebrew first.${NC}"
elif command -v gh &> /dev/null; then
    echo -e "${GREEN}✓${NC} gh is already installed."
else
    if brew install gh; then
        echo -e "${GREEN}✓${NC} gh installed successfully via Homebrew."
    else
        echo -e "${RED}Error: Failed to install gh via Homebrew.${NC}"
    fi
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

# Install Ollama
echo
echo -e "${CYAN}Installing Ollama...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓${NC} Ollama is already installed."
elif command -v brew &> /dev/null; then
    if brew install ollama; then
        echo -e "${GREEN}✓${NC} Ollama installed successfully via Homebrew."
    else
        echo -e "${RED}Error: Failed to install Ollama via Homebrew.${NC}"
    fi
elif command -v curl &> /dev/null; then
    echo -e "${CYAN}Attempting to install Ollama via install script...${NC}"
    if curl -fsSL https://ollama.com/install.sh | sh; then
        echo -e "${GREEN}✓${NC} Ollama installed successfully."
    else
        echo -e "${RED}Error: Failed to install Ollama via install script.${NC}"
    fi
else
    echo -e "${YELLOW}! Neither Homebrew nor curl found; skipping Ollama install.${NC}"
    echo -e "${YELLOW}  Please install Ollama manually from https://ollama.com${NC}"
fi

# Install Aider
echo
echo -e "${CYAN}Installing Aider AI pair programming tool...${NC}"
if command -v aider &> /dev/null; then
    echo -e "${GREEN}✓${NC} Aider is already installed."
else
    if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
        PYTHON_PIP=$(command -v pip3 || command -v pip)
        echo -e "${CYAN}Installing Aider via pip...${NC}"
        if $PYTHON_PIP install aider-chat; then
            echo -e "${GREEN}✓${NC} Aider installed successfully."
        else
            echo -e "${RED}Error: Failed to install Aider.${NC}"
        fi
    else
        echo -e "${YELLOW}! pip not found; skipping Aider install.${NC}"
        echo -e "${YELLOW}  Install Python 3 and pip, then run: pip install aider-chat${NC}"
    fi
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
