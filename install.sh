#!/bin/bash

# AI Development Environment Installer
# Installs the ai command globally for universal AI tool launching

set -euo pipefail

# Configuration - unified under ~/.local/ai-dev
BASE_DIR="$HOME/.local/ai-dev"
CONFIG_DIR="$BASE_DIR"
INSTALL_DIR="$BASE_DIR"
BIN_DIR="$BASE_DIR/bin"
ENV_FILE="$BASE_DIR/.env"
MCP_FILE="$BASE_DIR/mcp.json"
REPO_URL="${AI_DEV_REPO_URL:-https://gitlab.checkrhq.net/foundations/delivery-platform/dev-productivity/ai-developer}"
SCRIPT_NAME="ai"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

copy_mcp_templates() {
    local profiles_dir="$BASE_DIR/mcp-profiles"
    local layers_dir="$BASE_DIR/mcp-layers"
    mkdir -p "$profiles_dir" "$layers_dir"

    # Clean up old profile names (migration from old naming)
    if [[ -f "$profiles_dir/memory.mcp.json" ]]; then
        log_info "Removing old memory.mcp.json profile (renamed to persistent.mcp.json)"
        rm -f "$profiles_dir/memory.mcp.json"
    fi

    # Copy MCP base layers from templates
    if [[ -d "templates/mcp-layers" ]]; then
        cp -r templates/mcp-layers/* "$layers_dir/"
        log_success "Copied MCP base layers from templates"
    else
        log_error "MCP layers templates not found in templates/mcp-layers/"
        return 1
    fi

    # Copy MCP profiles from templates  
    if [[ -d "templates/mcp-profiles" ]]; then
        cp -r templates/mcp-profiles/* "$profiles_dir/"
        log_success "Copied MCP profiles from templates"
    else
        log_error "MCP profiles templates not found in templates/mcp-profiles/"
        return 1
    fi

    # Make global mcp.json point to default profile
    ln -sfn "$profiles_dir/default.mcp.json" "$MCP_FILE"
    log_success "Set default MCP profile symlink -> $MCP_FILE"
}

# Check if running in CI or if files are local
detect_installation_mode() {
    # Always prefer local if files exist in current directory
    if [[ -f "bin/ai" ]]; then
        echo "local"
    # Check if we're in the installed copy - fallback to remote installation
    # (removed hardcoded path since we now have proper GitLab hosting)
    else
        echo "remote"
    fi
}

do_shared_installation() {
    # Create unified directory structure
    mkdir -p "$BASE_DIR"
    mkdir -p "$BIN_DIR"
    mkdir -p "$BASE_DIR/templates"
    mkdir -p "$BASE_DIR/memory-banks"
    
    # Copy core files (assumes they exist in current directory)
    # NOTE: do NOT copy a top-level templates/mcp.json here; $MCP_FILE is a symlink to default profile
    # Use profiles written by write_profiles() instead.
    cp bin/ai "$BIN_DIR/$SCRIPT_NAME"
    cp bin/ai-utils.sh "$BIN_DIR/"
    cp bin/ai-core.sh "$BIN_DIR/"
    cp bin/ai-project.sh "$BIN_DIR/"
    chmod +x "$BIN_DIR/$SCRIPT_NAME"
    chmod +x "$BIN_DIR/ai-utils.sh"
    chmod +x "$BIN_DIR/ai-core.sh"
    chmod +x "$BIN_DIR/ai-project.sh"

    # Copy all templates for global availability (e.g., engineering-workflow.md)
    if [[ -d "templates" ]]; then
        # Clear existing templates directory to prevent accumulation of old files
        rm -rf "$BASE_DIR/templates"
        mkdir -p "$BASE_DIR/templates"
        # Copy the entire templates directory contents into the global templates dir
        cp -R "templates/." "$BASE_DIR/templates/"
    fi
    
    # Copy install script for future updates
    cp install.sh "$BASE_DIR/install.sh"
    chmod +x "$BASE_DIR/install.sh"
}

install_from_local() {
    log_info "Installing from local files..."
    
    # Do shared installation steps
    do_shared_installation
    
    # Copy MCP templates and set default symlink
    copy_mcp_templates
    

    # Create global environment file template with variable substitution
    if [[ ! -f "$ENV_FILE" ]]; then
        # Load local .env file if it exists for template substitution
        if [[ -f ".env" ]]; then
            log_info "Loading local .env file for template substitution..."
            source .env
        else
            log_warning "No .env file found. Please copy .env.template to .env and fill in your credentials."
            log_info "Then run ./install.sh again to create the global environment file."
            log_info "Example: cp .env.template .env && ./install.sh"
        fi
        
        # Use .env.template as the source and convert to variable substitution format
        if [[ -f ".env.template" ]]; then
            log_info "Creating global environment file from .env.template..."
            {
                echo "# ============================================================================="
                echo "# Shared AI Development Environment Variables"  
                echo "# ============================================================================="
                echo "# This file contains environment variables shared across all projects"
                echo "# Generated from .env.template with variable substitution format"
                echo ""
                
                # Process .env.template and convert to variable substitution format
                while IFS= read -r line; do
                    # Skip comments and empty lines, but preserve them
                    if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
                        echo "$line"
                    elif [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
                        # Extract variable name and value
                        var_name="${BASH_REMATCH[1]}"
                        var_value="${BASH_REMATCH[2]}"
                        
                        # Preserve quotes if the original value was quoted, or add quotes if value contains spaces
                        if [[ "$var_value" =~ ^\".*\"$ ]] || [[ "$var_value" =~ ^\'.*\'$ ]]; then
                            # Value was already quoted, keep it quoted
                            echo "${var_name}=\${${var_name}:-${var_value}}"
                        elif [[ "$var_value" =~ [[:space:]] ]]; then
                            # Value contains spaces, add quotes
                            echo "${var_name}=\${${var_name}:-\"${var_value}\"}"
                        else
                            # Simple value, no quotes needed
                            echo "${var_name}=\${${var_name}:-${var_value}}"
                        fi
                    else
                        echo "$line"
                    fi
                done < ".env.template"
                
                echo ""
                echo "# ============================================================================="
                echo "# Instructions:"
                echo "# 1. Replace any remaining placeholder values with your real credentials"
                echo "# 2. These variables will be available in all projects"
                echo "# 3. Local .env files can override these global variables"
                echo "# ============================================================================="
            } > "$ENV_FILE"
        else
            log_error ".env.template not found! Cannot create global environment file."
            log_info "Expected .env.template to exist in the current directory."
            return 1
        fi
        
        # Process the template with variable substitution
        if command -v envsubst >/dev/null 2>&1; then
            envsubst < "$ENV_FILE" > "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"
            log_success "Created shared AI environment file with variable substitution"
        else
            log_warning "envsubst not found, using fallback variable substitution"
            # Fallback: use sed to replace common variables
            sed -i.bak \
                -e "s/\${GITLAB_TOKEN}/${GITLAB_TOKEN:-}/g" \
                -e "s/\${GITLAB_URL}/${GITLAB_URL:-}/g" \
                -e "s/\${GITLAB_API_URL}/${GITLAB_API_URL:-}/g" \
                -e "s/\${GITLAB_PERSONAL_ACCESS_TOKEN}/${GITLAB_PERSONAL_ACCESS_TOKEN:-}/g" \
                -e "s/\${GIT_AUTHOR_NAME}/${GIT_AUTHOR_NAME:-}/g" \
                -e "s/\${GIT_AUTHOR_EMAIL}/${GIT_AUTHOR_EMAIL:-}/g" \
                "$ENV_FILE" 2>/dev/null || true
            rm -f "$ENV_FILE.bak" 2>/dev/null || true
            log_success "Created shared AI environment file with fallback substitution"
        fi
        
        log_success "Created shared AI environment file at $ENV_FILE"
        log_info "Please review and update any remaining placeholder values"
    else
        log_success "Shared AI environment file already exists"
    fi
    
    # Install MCP servers
    if [[ -d "mcp-servers/retire-e2e-tests" ]]; then
        # Create the target directory structure
        mkdir -p "$BASE_DIR/mcp-servers/retire-e2e-tests"
        
        # Copy the entire retire-e2e-tests directory
        cp -r mcp-servers/retire-e2e-tests/* "$BASE_DIR/mcp-servers/retire-e2e-tests/"
        
        # Install dependencies if needed
        if [[ -f "$BASE_DIR/mcp-servers/retire-e2e-tests/package.json" ]]; then
            cd "$BASE_DIR/mcp-servers/retire-e2e-tests"
            npm install --silent
            cd - > /dev/null
        fi
        
        log_success "Installed Test Overlap Analyzer MCP server (TypeScript)"
    elif [[ -f "examples/test-overlap-analyzer-mcp.js" ]]; then
        cp examples/test-overlap-analyzer-mcp.js "$BASE_DIR/"
        chmod +x "$BASE_DIR/test-overlap-analyzer-mcp.js"
        log_success "Installed Test Overlap Analyzer MCP server (JavaScript)"
    fi
    
    # Install additional tools
    install_claude_cli
    install_cursor_cli
    install_k8s_mcp_server
    
    log_success "Installed from local files"
}


install_from_remote() {
    log_info "Installing from GitLab repository..."
    
    # Create temporary directory  
    local temp_dir=$(mktemp -d)
    cd "$temp_dir"
    
    # Try SSH first, then HTTPS
    local ssh_url="git@gitlab.checkrhq.net:foundations/delivery-platform/dev-productivity/ai-developer.git"
    local https_url="$REPO_URL.git"
    
    if command -v git >/dev/null 2>&1; then
        log_info "Trying SSH clone (recommended for internal repos)..."
        if git clone --depth 1 "$ssh_url" . 2>/dev/null; then
            log_success "Successfully cloned via SSH"
        else
            log_warning "SSH clone failed, trying HTTPS..."
            log_info "Cloning from $https_url"
            if ! git clone --depth 1 "$https_url" .; then
                log_error "Both SSH and HTTPS clone failed."
                log_error "For internal GitLab repos, you need either:"
                log_error "  1. SSH keys configured: ssh-keygen -t ed25519 -C 'your_email@checkr.com'"
                log_error "  2. Personal access token configured in git credentials"
                log_error "  3. Clone the repo manually and run ./install.sh from the project directory"
                log_error ""
                log_error "Manual installation:"
                log_error "  git clone $ssh_url"
                log_error "  cd ai-developer"
                log_error "  ./install.sh"
                cd - > /dev/null 2>&1 || true
                rm -rf "$temp_dir" 2>/dev/null || true
                exit 1
            fi
        fi
    else
        log_error "Git is required but not found. Please install git."
        exit 1
    fi
    
    # Do shared installation steps
    do_shared_installation
    
    # Copy MCP templates and set default symlink
    copy_mcp_templates

    # Create global environment file template with variable substitution
    if [[ ! -f "$ENV_FILE" ]]; then
        # Load local .env file if it exists for template substitution
        if [[ -f ".env" ]]; then
            log_info "Loading local .env file for template substitution..."
            source .env
        else
            log_warning "No .env file found. Please copy .env.template to .env and fill in your credentials."
            log_info "Then run ./install.sh again to create the global environment file."
            log_info "Example: cp .env.template .env && ./install.sh"
        fi
        
        # Use .env.template as the source and convert to variable substitution format
        if [[ -f ".env.template" ]]; then
            log_info "Creating global environment file from .env.template..."
            {
                echo "# ============================================================================="
                echo "# Shared AI Development Environment Variables"  
                echo "# ============================================================================="
                echo "# This file contains environment variables shared across all projects"
                echo "# Generated from .env.template with variable substitution format"
                echo ""
                
                # Process .env.template and convert to variable substitution format
                while IFS= read -r line; do
                    # Skip comments and empty lines, but preserve them
                    if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]]; then
                        echo "$line"
                    elif [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
                        # Extract variable name and value
                        var_name="${BASH_REMATCH[1]}"
                        var_value="${BASH_REMATCH[2]}"
                        
                        # Preserve quotes if the original value was quoted, or add quotes if value contains spaces
                        if [[ "$var_value" =~ ^\".*\"$ ]] || [[ "$var_value" =~ ^\'.*\'$ ]]; then
                            # Value was already quoted, keep it quoted
                            echo "${var_name}=\${${var_name}:-${var_value}}"
                        elif [[ "$var_value" =~ [[:space:]] ]]; then
                            # Value contains spaces, add quotes
                            echo "${var_name}=\${${var_name}:-\"${var_value}\"}"
                        else
                            # Simple value, no quotes needed
                            echo "${var_name}=\${${var_name}:-${var_value}}"
                        fi
                    else
                        echo "$line"
                    fi
                done < ".env.template"
                
                echo ""
                echo "# ============================================================================="
                echo "# Instructions:"
                echo "# 1. Replace any remaining placeholder values with your real credentials"
                echo "# 2. These variables will be available in all projects"
                echo "# 3. Local .env files can override these global variables"
                echo "# ============================================================================="
            } > "$ENV_FILE"
        else
            log_error ".env.template not found! Cannot create global environment file."
            log_info "Expected .env.template to exist in the current directory."
            return 1
        fi
        
        # Process the template with variable substitution
        if command -v envsubst >/dev/null 2>&1; then
            envsubst < "$ENV_FILE" > "$ENV_FILE.tmp" && mv "$ENV_FILE.tmp" "$ENV_FILE"
            log_success "Created shared AI environment file with variable substitution"
        else
            log_warning "envsubst not found, using fallback variable substitution"
            # Fallback: use sed to replace common variables
            sed -i.bak \
                -e "s/\${GITLAB_TOKEN}/${GITLAB_TOKEN:-}/g" \
                -e "s/\${GITLAB_URL}/${GITLAB_URL:-}/g" \
                -e "s/\${GITLAB_API_URL}/${GITLAB_API_URL:-}/g" \
                -e "s/\${GITLAB_PERSONAL_ACCESS_TOKEN}/${GITLAB_PERSONAL_ACCESS_TOKEN:-}/g" \
                -e "s/\${GIT_AUTHOR_NAME}/${GIT_AUTHOR_NAME:-}/g" \
                -e "s/\${GIT_AUTHOR_EMAIL}/${GIT_AUTHOR_EMAIL:-}/g" \
                "$ENV_FILE" 2>/dev/null || true
            rm -f "$ENV_FILE.bak" 2>/dev/null || true
            log_success "Created shared AI environment file with fallback substitution"
        fi
        
        log_success "Created shared AI environment file at $ENV_FILE"
        log_info "Please review and update any remaining placeholder values"
    else
        log_success "Shared AI environment file already exists"
    fi
    
    # Install MCP servers
    if [[ -d "mcp-servers/retire-e2e-tests" ]]; then
        # Create the target directory structure
        mkdir -p "$BASE_DIR/mcp-servers/retire-e2e-tests"
        
        # Copy the entire retire-e2e-tests directory
        cp -r mcp-servers/retire-e2e-tests/* "$BASE_DIR/mcp-servers/retire-e2e-tests/"
        
        # Install dependencies if needed
        if [[ -f "$BASE_DIR/mcp-servers/retire-e2e-tests/package.json" ]]; then
            cd "$BASE_DIR/mcp-servers/retire-e2e-tests"
            npm install --silent
            cd - > /dev/null
        fi
        
        log_success "Installed Test Overlap Analyzer MCP server (TypeScript)"
    elif [[ -f "examples/test-overlap-analyzer-mcp.js" ]]; then
        cp examples/test-overlap-analyzer-mcp.js "$BASE_DIR/"
        chmod +x "$BASE_DIR/test-overlap-analyzer-mcp.js"
        log_success "Installed Test Overlap Analyzer MCP server (JavaScript)"
    fi
    
    # Install additional tools
    install_claude_cli
    install_cursor_cli
    install_k8s_mcp_server
    
    # Cleanup
    cd /
    rm -rf "$temp_dir"
    
    log_success "Installed from remote repository"
}

install_claude_cli() {
    log_info "Installing Claude CLI..."
    
    # Check if claude command already exists
    if command -v claude >/dev/null 2>&1; then
        log_success "Claude CLI already installed"
        return 0
    fi
    
    # Install Claude CLI using the official installer
    if command -v curl >/dev/null 2>&1; then
        log_info "Using curl to install Claude CLI..."
        if curl -sSL https://claude.ai/install.sh | bash; then
            log_success "Installed Claude CLI successfully"
        else
            log_warning "Claude CLI installation failed via curl, trying alternative method..."
            # Try npm installation as fallback
            if command -v npm >/dev/null 2>&1; then
                if npm install -g @anthropics/claude-cli; then
                    log_success "Installed Claude CLI via npm"
                else
                    log_warning "Claude CLI installation failed via npm"
                    return 1
                fi
            else
                log_warning "npm not found. Cannot install Claude CLI automatically."
                log_info "Please install npm or manually install Claude CLI from https://claude.ai/cli"
                return 1
            fi
        fi
    else
        log_warning "curl not found. Cannot install Claude CLI automatically."
        log_info "Please install curl or manually install Claude CLI from https://claude.ai/cli"
        return 1
    fi
    
    # Verify installation
    if command -v claude >/dev/null 2>&1; then
        log_success "Claude CLI installed and verified"
        return 0
    else
        log_warning "Claude CLI installation may have failed - command not found"
        log_info "You may need to restart your terminal or source your shell profile"
        return 1
    fi
}

install_cursor_cli() {
    log_info "Installing Cursor CLI..."
    
    # Check if cursor command already exists
    if command -v cursor >/dev/null 2>&1; then
        log_success "Cursor CLI already installed"
        return 0
    fi
    
    # Install Cursor CLI using the official installer
    if command -v curl >/dev/null 2>&1; then
        log_info "Using curl to install Cursor CLI..."
        if curl https://cursor.com/install -fsS | bash; then
            log_success "Installed Cursor CLI successfully"
        else
            log_warning "Cursor CLI installation failed via curl"
            return 1
        fi
    else
        log_warning "curl not found. Cannot install Cursor CLI automatically."
        log_info "Please install curl or manually install Cursor CLI from https://cursor.com/cli"
        return 1
    fi
    
    # Verify installation
    if command -v cursor >/dev/null 2>&1; then
        log_success "Cursor CLI installed and verified"
        return 0
    else
        log_warning "Cursor CLI installation may have failed - command not found"
        log_info "You may need to restart your terminal or source your shell profile"
        return 1
    fi
}

install_k8s_mcp_server() {
    log_info "Installing k8s MCP server..."
    
    # Check if Go is available
    if command -v go >/dev/null 2>&1; then
        log_info "Using go install to install k8s MCP server..."
        
        # Use go install to get the latest version
        if GOBIN="$BIN_DIR" go install github.com/reza-gholizade/k8s-mcp-server@latest; then
            log_success "Installed k8s MCP server using go install"
        else
            log_warning "go install failed, trying to build from source..."
            
            # Fallback: Build from source
            local temp_dir=$(mktemp -d)
            cd "$temp_dir"
            
            # Clone the repository
            if command -v git >/dev/null 2>&1; then
                git clone https://github.com/reza-gholizade/k8s-mcp-server.git .
            else
                # Download source as tar.gz
                if command -v curl >/dev/null 2>&1; then
                    curl -fsSL https://github.com/reza-gholizade/k8s-mcp-server/archive/main.tar.gz | tar -xz --strip-components=1
                elif command -v wget >/dev/null 2>&1; then
                    wget -qO- https://github.com/reza-gholizade/k8s-mcp-server/archive/main.tar.gz | tar -xz --strip-components=1
                else
                    log_error "Neither git, curl, nor wget found."
                    cd - > /dev/null
                    rm -rf "$temp_dir"
                    return 1
                fi
            fi
            
            # Build the binary
            go build -o "$BIN_DIR/k8s-mcp-server" . || {
                log_error "Failed to build k8s MCP server"
                cd - > /dev/null
                rm -rf "$temp_dir"
                return 1
            }
            
            cd - > /dev/null
            rm -rf "$temp_dir"
            
            log_success "Built and installed k8s MCP server from source"
        fi
    else
        log_warning "Go not found. k8s MCP server requires Go to be installed."
        log_info "Please install Go from https://golang.org/dl/ and run the installer again."
        log_info "Alternatively, you can manually install the k8s MCP server binary to $BIN_DIR/k8s-mcp-server"
        return 1
    fi
    
    # Verify installation
    if [[ -f "$BIN_DIR/k8s-mcp-server" && -x "$BIN_DIR/k8s-mcp-server" ]]; then
        log_success "k8s MCP server installed successfully"
        return 0
    else
        log_warning "k8s MCP server installation may have failed"
        return 1
    fi
}

check_dependencies() {
    log_info "Checking dependencies..."
    
    # Check for bash
    if ! command -v bash >/dev/null 2>&1; then
        log_error "bash is required but not found"
        exit 1
    fi
    
    # Check for basic tools
    local missing_tools=()
    
    if ! command -v curl >/dev/null 2>&1 && ! command -v wget >/dev/null 2>&1; then
        missing_tools+=("curl or wget")
    fi
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_warning "Some tools are missing: ${missing_tools[*]}"
        log_info "The installer will continue, but some features may not work"
    fi
    
    log_success "Dependency check completed"
}

setup_path() {
    # Check if ~/.local/bin is in PATH
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        log_warning "$BIN_DIR is not in your PATH"
        
        # Try to add to shell profile - detect actual shell being used
        local shell_profile=""
        local current_shell=$(basename "$SHELL")
        
        case "$current_shell" in
            "zsh")
                shell_profile="$HOME/.zshrc"
                ;;
            "bash")
                shell_profile="$HOME/.bashrc"
                ;;
            "fish")
                shell_profile="$HOME/.config/fish/config.fish"
                ;;
            *)
                # Fallback: check which profiles exist
                if [[ -f "$HOME/.zshrc" ]]; then
                    shell_profile="$HOME/.zshrc"
                elif [[ -f "$HOME/.bashrc" ]]; then
                    shell_profile="$HOME/.bashrc"
                elif [[ -f "$HOME/.bash_profile" ]]; then
                    shell_profile="$HOME/.bash_profile"
                fi
                ;;
        esac
        
        if [[ -n "$shell_profile" ]]; then
            log_info "Adding $BIN_DIR to PATH in $shell_profile"
            echo 'export PATH="$HOME/.local/ai-dev/bin:$PATH"' >> "$shell_profile"
            log_success "Updated $shell_profile"
            log_warning "Please run 'source $shell_profile' or restart your terminal"
        else
            log_warning "Could not detect shell. Please manually add this to your shell profile:"
            echo 'export PATH="$HOME/.local/ai-dev/bin:$PATH"'
        fi
    else
        log_success "PATH is already configured correctly"
    fi
}

verify_installation() {
    log_info "Verifying installation..."
    
    # Check if files exist
    if [[ ! -f "$BIN_DIR/$SCRIPT_NAME" ]]; then
        log_error "Installation failed: $BIN_DIR/$SCRIPT_NAME not found"
        exit 1
    fi
    
    if [[ ! -f "$MCP_FILE" ]]; then
        log_error "Installation failed: $MCP_FILE not found"
        exit 1
    fi
    
    # Check if script is executable
    if [[ ! -x "$BIN_DIR/$SCRIPT_NAME" ]]; then
        log_error "Installation failed: $BIN_DIR/$SCRIPT_NAME is not executable"
        exit 1
    fi
    
    log_success "Installation verified successfully"
}

show_next_steps() {
    echo ""
    log_success "🎉 AI Development Environment installed successfully!"
    echo ""
    log_info "🚀 Next Steps:"
    echo "  1. If you have a .env file with credentials, sync them to AI environment:"
    echo "     ai env-sync"
    echo ""
    echo "  2. Configure any remaining AI development credentials:"
    echo "     ai setup"
    echo ""
    echo "  3. Initialize any project with AI tools:"
    echo "     cd my-project && ai init"
    echo ""
    echo "  4. Launch AI tools:"
    echo "     ai claude      # Claude Code (desktop app)"
    echo "     ai claude-app   # Claude Desktop app"
    echo "     ai cursor       # Cursor CLI (cursor-agent)"
    echo "     ai cursor-app   # Cursor app (full editor)"
    echo ""
    log_info "📖 Available Commands:"
    echo "  ai init              # Initialize project with AI tools"
    echo "  ai claude            # Launch Claude Code (desktop app)"
    echo "  ai claude-app        # Launch Claude Desktop app"
    echo "  ai cursor            # Launch Cursor CLI (cursor-agent)"
    echo "  ai cursor-app        # Launch Cursor app (full editor)"
    echo "  ai check             # Check environment setup"
    echo "  ai help              # Show detailed help"
    echo ""
    log_info "🔧 Configuration:"
    echo "  Global config: $CONFIG_DIR"
    echo "  Environment file: $ENV_FILE"
    echo "  MCP config: $MCP_FILE"
    echo "  Install location: $BIN_DIR/$SCRIPT_NAME"
    echo ""
    
    # Show version info if we can detect it
    if command -v "$SCRIPT_NAME" >/dev/null 2>&1; then
        echo "✅ Ready to use! Try: ai help"
    else
        log_warning "Command not found in PATH. Please restart your terminal or source your shell profile."
    fi
}

main() {
    echo "🤖 AI Development Environment Installer"
    echo ""
    
    # Check dependencies
    check_dependencies
    
    # Detect installation mode and install
    local mode=$(detect_installation_mode)
    
    case "$mode" in
        "local")
            install_from_local
            ;;
        "remote")
            install_from_remote
            ;;
        *)
            log_error "Unknown installation mode"
            exit 1
            ;;
    esac
    
    # Setup PATH
    setup_path
    
    # Verify installation
    verify_installation
    
    # Show next steps
    show_next_steps
}

# Handle command line options
case "${1:-}" in
    "--help"|"-h")
        echo "AI Development Environment Installer"
        echo ""
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h           Show this help"
        echo "  --version VERSION    Install specific version (default: main)"
        echo ""
        echo "Environment Variables:"
        echo "  AI_DEV_REPO_URL     GitLab repository URL"
        echo "  AI_DEV_VERSION      Version/tag to install"
        echo ""
        echo "Examples:"
        echo "  $0                           # Install latest"
        echo "  AI_DEV_VERSION=v1.0.0 $0    # Install specific version"
        exit 0
        ;;
    "--version")
        if [[ -z "${2:-}" ]]; then
            log_error "--version requires a version argument"
            exit 1
        fi
        export AI_DEV_VERSION="$2"
        ;;
esac

# Run main installation
main "$@"