#!/bin/bash

# AI Development Environment - Project Management
# This module contains project initialization, workflow, and sync functions

# Source utility functions
source "$(dirname "${BASH_SOURCE[0]}")/ai-utils.sh"

# Create MCP servers file
create_mcp_servers_file() {
    local servers_file="mcp-servers-to-add.json"
    
    log_info "Creating separate MCP servers file for easy merging..."
    
    # Create the servers-only JSON file
    cat > "$servers_file" << 'EOF'
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    },
    "git": {
      "command": "git-mcp-server",
      "args": []
    },
    "gitlab": {
      "command": "npx",
      "args": ["-y", "@zereight/mcp-gitlab"],
      "env": {
        "GITLAB_PERSONAL_ACCESS_TOKEN": "${GITLAB_PERSONAL_ACCESS_TOKEN}",
        "GITLAB_API_URL": "${GITLAB_API_URL:-https://gitlab.com/api/v4}",
        "GITLAB_READ_ONLY_MODE": "${GITLAB_READ_ONLY_MODE:-false}",
        "USE_GITLAB_WIKI": "${USE_GITLAB_WIKI:-true}",
        "USE_MILESTONE": "${USE_MILESTONE:-true}",
        "USE_PIPELINE": "${USE_PIPELINE:-true}"
      }
    },
    "atlassian": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://mcp.atlassian.com/v1/sse"]
    },
    "serena": {
      "command": "npx",
      "args": ["-y", "@oraios/serena"]
    },
    "memory-bank": {
      "command": "npx",
      "args": ["-y", "@alioshr/memory-bank-mcp"],
      "env": {
        "MEMORY_BANK_ROOT": "${MEMORY_BANK_ROOT:-${HOME}/.local/ai-dev/memory-banks}"
      }
    },
    "duckduckgo": {
      "command": "uvx",
      "args": ["duckduckgo-mcp-server"]
    },
    "sequentialthinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequentialthinking"]
    },
    "compass": {
      "command": "npx",
      "args": ["-y", "@liuyoshio/mcp-compass"]
    },
    "heimdall": {
      "command": "npx",
      "args": ["-y", "@shinzo-labs/heimdall"]
    },
    "test-overlap-analyzer": {
      "command": "npx",
      "args": ["tsx", "${HOME}/.local/ai-dev/mcp-servers/retire-e2e-tests/index.ts"]
    },
    "k8s": {
      "command": "k8s-mcp-server",
      "args": ["--mode", "stdio"],
      "env": {
        "KUBECONFIG": "${KUBECONFIG:-${HOME}/.kube/config}"
      }
    },
    "cypress": {
      "command": "node",
      "args": ["${HOME}/.local/share/cypress-mcp-server/src/index.js"]
    }
  }
}
EOF
    
    log_success "Created $servers_file with AI dev MCP servers"
    log_info "💡 To add these servers to your existing MCP config:"
    log_info "   1. View the servers: cat $servers_file"
    log_info "   2. Copy the servers you want from the 'mcpServers' section"
    log_info "   3. Add them to your existing .mcp.json or .cursor/mcp.json"
    log_info "   4. Delete $servers_file when done"
}

# Set up Claude Sub Agents
setup_claude_agents() {
    local agents_dir=".claude/agents"
    local templates_dir=""
    
    # Find templates directory (prefer global over local to avoid duplicates)
    if [[ -d "$CONFIG_DIR/templates/agents" ]]; then
        templates_dir="$CONFIG_DIR/templates/agents"
        log_info "Using global agent templates from $CONFIG_DIR/templates/agents"
    elif [[ -d "$(dirname "${BASH_SOURCE[0]}")/../templates/agents" ]]; then
        templates_dir="$(dirname "${BASH_SOURCE[0]}")/../templates/agents"
        log_info "Using local agent templates from $(dirname "${BASH_SOURCE[0]}")/../templates/agents"
    fi
    
    if [[ -n "$templates_dir" && -d "$templates_dir" ]]; then
        log_info "Setting up Claude Sub Agents..."
        mkdir -p "$agents_dir"
        
        # Copy agent templates if they don't exist
        local agents_copied=0
        for agent_template in "$templates_dir"/*.md; do
            if [[ -f "$agent_template" ]]; then
                local agent_name=$(basename "$agent_template")
                if [[ ! -f "$agents_dir/$agent_name" ]]; then
                    cp "$agent_template" "$agents_dir/"
                    ((agents_copied++))
                    log_info "Copied $agent_name from $templates_dir"
                fi
            fi
        done
        
        if [[ $agents_copied -gt 0 ]]; then
            log_success "Copied $agents_copied Claude Sub Agent templates to $agents_dir"
            log_info "Available agents:"
            for agent_file in "$agents_dir"/*.md; do
                if [[ -f "$agent_file" ]]; then
                    local agent_name=$(basename "$agent_file" .md)
                    echo "  🤖 $agent_name"
                fi
            done
        else
            log_info "Claude Sub Agents already exist in $agents_dir"
        fi
    else
        log_info "No agent templates found, skipping Sub Agent setup"
    fi
}

# Initialize project
init_project() {
    log_info "Initializing AI development project in $(pwd)"
    
    # Load global environment variables for template processing
    if [[ -f "$GLOBAL_ENV_FILE" ]]; then
        log_info "Loading shared AI environment variables for template processing..."
        source "$GLOBAL_ENV_FILE"
        log_success "Shared AI environment variables loaded"
    else
        log_warning "No shared AI environment file found at $GLOBAL_ENV_FILE"
        log_info "💡 To set up global environment variables:"
        log_info "   1. Edit $GLOBAL_ENV_FILE with your credentials"
        log_info "   2. Or run 'ai init' in a new project to create a template"
    fi
    
    # Create .claude directory and MCP symlink for Claude Code
    mkdir -p .claude
    
    # Set up Claude Sub Agents
    setup_claude_agents
    
    if [[ ! -f ".claude/.mcp.json" ]]; then
        if [[ -f "$CONFIG_DIR/mcp.json" ]]; then
            # Create symlink to global config for Claude Code
            log_info "Creating .claude/.mcp.json symlink to global MCP configuration..."
            ln -sf "$CONFIG_DIR/mcp.json" ".claude/.mcp.json"
            log_success "Created .claude/.mcp.json symlink to global MCP configuration"
        else
            log_warning "Global MCP configuration not found, creating basic .claude/.mcp.json file"
            cat > ".claude/.mcp.json" << 'EOF'
{
  "mcpServers": {
    "git": {
      "command": "git-mcp-server",
      "args": []
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    },
    "test-overlap-analyzer": {
      "command": "npx",
      "args": ["tsx", "${HOME}/.local/ai-dev/mcp-servers/retire-e2e-tests/index.ts"]
    }
  }
}
EOF
        fi
    else
        if [[ -L ".claude/.mcp.json" ]]; then
            log_success ".claude/.mcp.json symlink already exists"
        else
            log_warning ".claude/.mcp.json already exists (not a symlink)"
            create_mcp_servers_file
        fi
    fi
    
    # Cursor also uses .cursor/mcp.json - create symlink
    mkdir -p .cursor
    if [[ ! -f ".cursor/mcp.json" ]]; then
        if [[ -f "$CONFIG_DIR/mcp.json" ]]; then
            log_info "Creating .cursor/mcp.json symlink..."
            ln -sf "$CONFIG_DIR/mcp.json" ".cursor/mcp.json"
            log_success "Created .cursor/mcp.json symlink"
        else
            log_warning "No global MCP configuration found to symlink to Cursor"
        fi
    else
        if [[ -L ".cursor/mcp.json" ]]; then
            log_success ".cursor/mcp.json symlink already exists"
        else
            log_warning ".cursor/mcp.json already exists (not a symlink)"
            create_mcp_servers_file
        fi
    fi
    
    # Note: AI development credentials are stored centrally in ~/.local/ai-dev/.env
    # No local .env file creation - keeps credentials centralized and secure
    
    # Load global environment variables into current shell session
    if [[ -f "$GLOBAL_ENV_FILE" ]]; then
        log_info "Loading shared AI environment variables into current shell session..."
        source "$GLOBAL_ENV_FILE"
        log_success "Shared AI environment variables loaded and exported to current shell"
    else
        log_warning "No shared AI environment file found at $GLOBAL_ENV_FILE"
        log_info "💡 Global variables will be loaded automatically once you create the file"
    fi
    
    # .claude/.mcp already handled above with symlink approach
    
    # Handle engineering workflow integration
    local templates_dir=""
    if [[ -d "$CONFIG_DIR/templates" ]]; then
        templates_dir="$CONFIG_DIR/templates"
    elif [[ -d "$(dirname "${BASH_SOURCE[0]}")/../templates" ]]; then
        templates_dir="$(dirname "${BASH_SOURCE[0]}")/../templates"
    fi
    
    if [[ -n "$templates_dir" && -f "$templates_dir/engineering-workflow.md" ]]; then
        # Create separate engineering workflow file in .claude directory
        if [[ ! -f ".claude/engineering-workflow.md" ]]; then
            log_info "Creating .claude/engineering-workflow.md..."
            cp "$templates_dir/engineering-workflow.md" ".claude/engineering-workflow.md"
            log_success "Created .claude/engineering-workflow.md"
        fi
        
        # Create CLAUDE.local.md with engineering workflow reference
        if [[ ! -f "CLAUDE.local.md" ]]; then
            log_info "Creating CLAUDE.local.md with engineering workflow reference..."
            cat > "CLAUDE.local.md" << 'EOF'
# Local AI Development Instructions

This file contains local development workflow instructions for AI tools.

---

📋 **Engineering Workflow**: See `.claude/engineering-workflow.md` for standard task completion workflow including JIRA integration, branching, and MR creation.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
EOF
            log_success "Created CLAUDE.local.md with engineering workflow reference"
        else
            # CLAUDE.local.md exists - check if workflow reference is already there
            if ! grep -q "engineering-workflow.md" "CLAUDE.local.md"; then
                log_info "Adding engineering workflow reference to existing CLAUDE.local.md..."
                echo "" >> "CLAUDE.local.md"
                echo "---" >> "CLAUDE.local.md"
                echo "" >> "CLAUDE.local.md"
                echo "📋 **Engineering Workflow**: See \`.claude/engineering-workflow.md\` for standard task completion workflow including JIRA integration, branching, and MR creation." >> "CLAUDE.local.md"
                log_success "Added engineering workflow reference to CLAUDE.local.md"
            else
                log_info "Engineering workflow reference already exists in CLAUDE.local.md"
            fi
        fi
    fi
    
    # Provide CLAUDE.md guidance
    if command -v claude >/dev/null 2>&1; then
        log_success "✅ Claude CLI detected"
        if [[ -f "CLAUDE.md" ]]; then
            log_info "💡 CLAUDE.md ready with engineering workflow integrated"
        else
            log_info "💡 To complete setup:"
            log_info "   1. Launch Claude Code: 'ai claude' or 'ai claude --profile <name>'"
            log_info "   2. Engineering workflow will auto-integrate next time you run 'ai init'"
        fi
        log_info "💡 Configs are already synced between Claude and Cursor!"
    else
        log_warning "'claude' CLI not found – install Claude Code for full functionality"
        log_info "💡 You can still use other AI tools like Cursor with the synced configs"
    fi

    # Create or update .cursor/rules.json to summarize CLAUDE.md
    mkdir -p .cursor
    local rules_file=".cursor/rules.json"

    if [[ ! -f "$rules_file" ]]; then
        cat > "$rules_file" << 'EOF'
{
  "include": ["**/*.rb", "**/*.py", "**/*.ts", "**/*.js", "**/*.go", "**/*.md"],
  "exclude": ["node_modules/**", "vendor/**", "log/**", "tmp/**"],
  "summarize": ["CLAUDE.md", "CLAUDE.local.md", ".claude/engineering-workflow.md"],
  "link": [],
  "rewrite": []
}
EOF
        log_success "Created .cursor/rules.json with CLAUDE.md, CLAUDE.local.md and engineering workflow summarized"
    else
        if check_jq; then
            if grep -q '"summarize"' "$rules_file"; then
                # Add CLAUDE.md if missing
                if ! grep -q 'CLAUDE\.md' "$rules_file"; then
                    tmpfile=$(mktemp)
                    jq '.summarize += ["CLAUDE.md"]' "$rules_file" > "$tmpfile" && mv "$tmpfile" "$rules_file"
                    log_success "Added CLAUDE.md to summarize in $rules_file"
                fi
                # Add CLAUDE.local.md if missing
                if ! grep -q 'CLAUDE\.local\.md' "$rules_file"; then
                    tmpfile=$(mktemp)
                    jq '.summarize += ["CLAUDE.local.md"]' "$rules_file" > "$tmpfile" && mv "$tmpfile" "$rules_file"
                    log_success "Added CLAUDE.local.md to summarize in $rules_file"
                fi
                # Add engineering workflow if missing
                if ! grep -q 'engineering-workflow\.md' "$rules_file"; then
                    tmpfile=$(mktemp)
                    jq '.summarize += [".claude/engineering-workflow.md"]' "$rules_file" > "$tmpfile" && mv "$tmpfile" "$rules_file"
                    log_success "Added engineering workflow to summarize in $rules_file"
                fi
            else
                tmpfile=$(mktemp)
                jq '. + { "summarize": ["CLAUDE.md", "CLAUDE.local.md", ".claude/engineering-workflow.md"] }' "$rules_file" > "$tmpfile" && mv "$tmpfile" "$rules_file"
                log_success "Added summarize section with CLAUDE.md, CLAUDE.local.md and engineering workflow to $rules_file"
            fi
        else
            log_warning "jq not available - cannot update existing $rules_file automatically"
            log_info "Please manually add 'CLAUDE.md' and '.claude/engineering-workflow.md' to the 'summarize' array in $rules_file"
        fi
    fi
    
    log_success "Project initialized!"
    log_info "Next steps:"
    log_info "1. Edit ~/.local/ai-dev/.env with your credentials (run 'ai setup' for guidance)"
    if command -v claude >/dev/null 2>&1; then
        log_info "2. Run 'ai claude [--profile <name>]' for Claude Code"
        log_info "3. Run 'ai cursor [--profile <name>]' for Cursor"
    else
        log_info "2. Run 'ai cursor [--profile <name>]' for Cursor (configs already set up!)"
        log_info "3. Install Claude Code for full functionality"
    fi
    log_info "4. Available profiles: default, persistent, devops, qa, research"
    log_info "5. Run 'ai help' for more profile options"
    exit 0
}

# Add engineering workflow
add_engineering_workflow() {
    log_info "Adding engineering workflow to CLAUDE.md in $(pwd)"
    
    # Find templates directory
    local templates_dir=""
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Try multiple possible locations
    local possible_templates=(
        "$CONFIG_DIR/templates"
        "$script_dir/../templates"
        "$script_dir/templates" 
    )
    
    for dir in "${possible_templates[@]}"; do
        if [[ -d "$dir" && -f "$dir/engineering-workflow.md" ]]; then
            templates_dir="$dir"
            break
        fi
    done
    
    # Check both templates and docs directories for engineering-workflow.md
    local workflow_file=""
    if [[ -f "$templates_dir/engineering-workflow.md" ]]; then
        workflow_file="$templates_dir/engineering-workflow.md"
    elif [[ -f "$CONFIG_DIR/docs/engineering-workflow.md" ]]; then
        workflow_file="$CONFIG_DIR/docs/engineering-workflow.md"
    fi
    
    if [[ -z "$workflow_file" ]]; then
        log_error "Engineering workflow template not found"
        log_info "Expected at: $CONFIG_DIR/templates/engineering-workflow.md or $CONFIG_DIR/docs/engineering-workflow.md"
        exit 1
    fi
    
    # Create separate engineering workflow file in .claude directory
    mkdir -p .claude
    if [[ ! -f ".claude/engineering-workflow.md" ]]; then
        log_info "Creating .claude/engineering-workflow.md..."
        cp "$workflow_file" ".claude/engineering-workflow.md"
        log_success "Created .claude/engineering-workflow.md"
    else
        log_info ".claude/engineering-workflow.md already exists"
    fi
    
    # Create CLAUDE.local.md with engineering workflow reference
    if [[ ! -f "CLAUDE.local.md" ]]; then
        log_info "Creating CLAUDE.local.md with engineering workflow reference..."
        cat > "CLAUDE.local.md" << 'EOF'
# Local AI Development Instructions

This file contains local development workflow instructions for AI tools.

---

📋 **Engineering Workflow**: See `.claude/engineering-workflow.md` for standard task completion workflow including JIRA integration, branching, and MR creation.
EOF
        log_success "Created CLAUDE.local.md with engineering workflow reference"
    else
        # CLAUDE.local.md exists - check if workflow reference is already there
        if ! grep -q "engineering-workflow.md" "CLAUDE.local.md"; then
            log_info "Adding engineering workflow reference to existing CLAUDE.local.md..."
            echo "" >> "CLAUDE.local.md"
            echo "---" >> "CLAUDE.local.md"
            echo "" >> "CLAUDE.local.md"
            echo "📋 **Engineering Workflow**: See \`.claude/engineering-workflow.md\` for standard task completion workflow including JIRA integration, branching, and MR creation." >> "CLAUDE.local.md"
            log_success "Added engineering workflow reference to CLAUDE.local.md"
        else
            log_warning "Engineering workflow reference already exists in CLAUDE.local.md"
        fi
    fi
    
    exit 0
}

# Install system
install_system() {
    log_info "Installing/updating AI development environment..."
    
    # Try multiple paths to find the install script
    local install_script
    install_script=$(find_install_script)
    
    if [[ -n "$install_script" ]]; then
        log_info "Running install script: $install_script"
        bash "$install_script"
    else
        log_error "Install script not found. Tried:"
        log_info ""
        log_info "💡 To fix this:"
        log_info "   1. Clone or download the ai-dev repository"
        log_info "   2. Run the install script directly from the project directory"
        log_info "   3. Or set up a symlink: ln -s /path/to/ai-dev/install.sh ~/.local/ai-dev/install.sh"
        exit 1
    fi
}

# Configure AI development credentials
setup_credentials() {
    log_info "🔧 Setting up AI development credentials..."
    
    # Check if global env file exists
    if [[ ! -f "$GLOBAL_ENV_FILE" ]]; then
        log_error "Global environment file not found: $GLOBAL_ENV_FILE"
        log_info "Please run 'ai install' first to create the environment file"
        return 1
    fi
    
    # Show current status
    echo ""
    log_info "📍 Your AI credentials are stored in: $GLOBAL_ENV_FILE"
    
    # Count variables
    local var_count=$(grep -c "^[A-Za-z_][A-Za-z0-9_]*=" "$GLOBAL_ENV_FILE" 2>/dev/null || echo "0")
    log_info "📊 Current variables: $var_count"
    
    # Show which variables need values
    echo ""
    log_info "🔍 Variables that need your actual values:"
    echo ""
    
    # Dynamically find placeholder values from the actual environment file
    local placeholder_lines=$(grep -E "(your-.*-here|Your Name|your-email@)" "$GLOBAL_ENV_FILE" 2>/dev/null || true)
    
    if [[ -n "$placeholder_lines" ]]; then
        while IFS= read -r line; do
            if [[ -n "$line" ]]; then
                local var_name=$(echo "$line" | cut -d'=' -f1)
                echo "  ❌ $var_name"
            fi
        done <<< "$placeholder_lines"
    else
        echo "  ✅ All variables appear to be configured"
    fi
    
    echo ""
    log_info "📝 To configure your credentials:"
    echo ""
    echo "  1. Open the file in your editor:"
    echo "     code ~/.local/ai-dev/.env"
    echo "     # or"
    echo "     vi ~/.local/ai-dev/.env"
    echo ""
    echo "  2. Replace placeholder values with your actual:"
    echo "     • GitLab personal access token"
    echo "     • Your name and email"
    echo ""
    echo "  3. Run 'ai check' to verify your setup"
    echo ""
    
    # Offer to open the file
    read -p "Would you like to open the credentials file now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v code >/dev/null 2>&1; then
            log_info "🚀 Opening credentials file in VS Code..."
            code "$GLOBAL_ENV_FILE"
        elif command -v vi >/dev/null 2>&1; then
            log_info "🚀 Opening credentials file in vi..."
            vi "$GLOBAL_ENV_FILE"
        else
            log_info "📍 Please edit this file: $GLOBAL_ENV_FILE"
        fi
    fi
}

# Sync configs
sync_configs() {
    log_info "Re-syncing Claude configs to Cursor format..."
    
    # Check if Claude config directory exists
    if [[ ! -d ".claude" ]]; then
        log_error "No .claude directory found. Run 'ai init' first to create Claude configs."
        exit 1
    fi
    
    # Create .cursor directory if it doesn't exist
    mkdir -p .cursor
    
    # Sync .claude/.mcp.json to .cursor/mcp.json if it exists
    if [[ -f ".claude/.mcp.json" ]]; then
        log_info "Re-syncing .claude/.mcp.json to .cursor/mcp.json..."
        cp ".claude/.mcp.json" ".cursor/mcp.json"
        log_success "Re-synced .claude/.mcp.json → .cursor/mcp.json"
    else
        log_warning "No .claude/.mcp.json file found"
    fi
    
    # Also check for legacy .claude/.mcp file
    if [[ -f ".claude/.mcp" ]]; then
        log_info "Re-syncing .claude/.mcp to .cursor/mcp.json..."
        cp ".claude/.mcp" ".cursor/mcp.json"
        log_success "Re-synced .claude/.mcp → .cursor/mcp.json"
    fi
    
    # Sync other potential Claude configs
    if [[ -f ".claude/settings.json" ]]; then
        log_info "Found .claude/settings.json - you may want to manually review for Cursor compatibility"
    fi
    
    # Ensure .cursor/rules.json includes both CLAUDE.md and engineering workflow
    local rules_file=".cursor/rules.json"
    if [[ -f "$rules_file" ]]; then
        if check_jq; then
            if grep -q '"summarize"' "$rules_file"; then
                # Add CLAUDE.md if missing
                if [[ -f "CLAUDE.md" ]] && ! grep -q 'CLAUDE\.md' "$rules_file"; then
                    tmpfile=$(mktemp)
                    jq '.summarize += ["CLAUDE.md"]' "$rules_file" > "$tmpfile" && mv "$tmpfile" "$rules_file"
                    log_success "Added CLAUDE.md to .cursor/rules.json summarize"
                fi
                # Add CLAUDE.local.md if missing
                if [[ -f "CLAUDE.local.md" ]] && ! grep -q 'CLAUDE\.local\.md' "$rules_file"; then
                    tmpfile=$(mktemp)
                    jq '.summarize += ["CLAUDE.local.md"]' "$rules_file" > "$tmpfile" && mv "$tmpfile" "$rules_file"
                    log_success "Added CLAUDE.local.md to .cursor/rules.json summarize"
                fi
                # Add engineering workflow if missing
                if [[ -f ".claude/engineering-workflow.md" ]] && ! grep -q 'engineering-workflow\.md' "$rules_file"; then
                    tmpfile=$(mktemp)
                    jq '.summarize += [".claude/engineering-workflow.md"]' "$rules_file" > "$tmpfile" && mv "$tmpfile" "$rules_file"
                    log_success "Added engineering workflow to .cursor/rules.json summarize"
                fi
            else
                # Create summarize array with available files
                local summarize_files=()
                [[ -f "CLAUDE.md" ]] && summarize_files+=("CLAUDE.md")
                [[ -f "CLAUDE.local.md" ]] && summarize_files+=("CLAUDE.local.md")
                [[ -f ".claude/engineering-workflow.md" ]] && summarize_files+=(".claude/engineering-workflow.md")
                
                if [[ ${#summarize_files[@]} -gt 0 ]]; then
                    tmpfile=$(mktemp)
                    jq --argjson files "$(printf '%s\n' "${summarize_files[@]}" | jq -R . | jq -s .)" '. + { "summarize": $files }' "$rules_file" > "$tmpfile" && mv "$tmpfile" "$rules_file"
                    log_success "Added summarize section to .cursor/rules.json"
                fi
            fi
        fi
    fi
    
    log_success "Config sync completed!"
    log_info "Claude and Cursor should now have consistent MCP configurations"
    log_info "💡 Note: 'ai init' now syncs configs automatically - 'ai sync' is mainly for re-syncing after manual changes"
}

# Sync local environment variables to global AI environment
 copy_env_to_global() {
    log_info "🔄 Syncing local environment variables to global AI environment..."
    
    local LOCAL_ENV="${LOCAL_ENV_FILE:-.env}"
    local GLOBAL_ENV="$HOME/.local/ai-dev/.env"
    
    # Check if global .env exists
    if [[ ! -f "$GLOBAL_ENV" ]]; then
        log_error "Global .env file not found: $GLOBAL_ENV"
        log_info "Please run 'ai install' first to create the global environment file"
        return 1
    fi
    
    # Create backup
    cp "$GLOBAL_ENV" "$GLOBAL_ENV.backup"
    log_info "💾 Backup created: $GLOBAL_ENV.backup"
    
    # Function to safely escape sed special characters
    escape_sed() {
        echo "$1" | sed 's/[[\.*^$()+?{|]/\\&/g'
    }
    
    # Function to update a single variable in the global file
    update_variable() {
        local var_name="$1"
        local var_value="$2"
        local placeholder_pattern="$3"
        
        # Skip if variable is empty or undefined
        if [[ -z "${var_value:-}" ]]; then
            log_info "⚠️  Skipping $var_name (empty or undefined)"
            return 0
        fi
        
        # Add quotes if the value contains spaces
        local final_value="$var_value"
        if [[ "$var_value" =~ [[:space:]] ]]; then
            final_value="\"$var_value\""
        fi
        
        # Escape special characters for sed
        local escaped_value=$(escape_sed "$final_value")
        local escaped_placeholder=$(escape_sed "$placeholder_pattern")
        
        # Update the global file
        if sed -i.tmp "s|$escaped_placeholder|$escaped_value|g" "$GLOBAL_ENV"; then
            log_info "✅ Updated $var_name"
        else
            log_error "❌ Failed to update $var_name"
            return 1
        fi
    }
    
    # Collect variables from available sources
    log_info "🔍 Collecting variables from available sources..."
    
    # Check if local .env exists and load it
    if [[ -f "$LOCAL_ENV" ]]; then
        log_info "📥 Loading variables from $LOCAL_ENV..."
        source "$LOCAL_ENV"
        
        # Get all variable names from local .env (excluding comments and empty lines)
        LOCAL_VARS=()
        while IFS='=' read -r line; do
            # Skip comments, empty lines, and lines without =
            if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]] || [[ ! "$line" =~ = ]]; then
                continue
            fi
            
            # Extract variable name (everything before first =)
            var_name="${line%%=*}"
            # Remove leading/trailing whitespace
            var_name=$(echo "$var_name" | xargs)
            
            if [[ -n "$var_name" ]]; then
                LOCAL_VARS+=("$var_name")
            fi
        done < "$LOCAL_ENV"
        
        log_info "📊 Found ${#LOCAL_VARS[@]} variables in $LOCAL_ENV"
    else
        log_info "⚠️  Local .env file not found: $LOCAL_ENV"
        log_info "💡 Checking for existing environment variables..."
        
        # Extract variable names from the global environment file
        LOCAL_VARS=()
        while IFS='=' read -r line; do
            # Skip comments, empty lines, and lines without =
            if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]] || [[ ! "$line" =~ = ]]; then
                continue
            fi
            
            # Extract variable name (everything before first =)
            var_name="${line%%=*}"
            # Remove leading/trailing whitespace
            var_name=$(echo "$var_name" | xargs)
            
            if [[ -n "$var_name" ]]; then
                LOCAL_VARS+=("$var_name")
            fi
        done < "$GLOBAL_ENV"
        
        # Filter to only include variables that actually exist
        EXISTING_VARS=()
        for var_name in "${LOCAL_VARS[@]}"; do
            if [[ -n "${!var_name:-}" ]]; then
                EXISTING_VARS+=("$var_name")
            fi
        done
        LOCAL_VARS=("${EXISTING_VARS[@]}")
        
        if [[ ${#LOCAL_VARS[@]} -eq 0 ]]; then
            log_error "❌ No variables found from any source"
            log_info "💡 Create a .env file or set environment variables before running this command"
            return 1
        fi
        
        log_info "📊 Found ${#LOCAL_VARS[@]} variables from environment"
    fi
    
    # Create a temporary working copy
    cp "$GLOBAL_ENV" "$GLOBAL_ENV.tmp"
    
    # Update each variable in the global file
    log_info "🔄 Updating global file with available values..."
    UPDATED_COUNT=0
    ERROR_COUNT=0
    
    # Get list of variables that exist in the AI environment file
    AI_ENV_VARS=()
    while IFS='=' read -r line; do
        # Skip comments, empty lines, and lines without =
        if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "$line" ]] || [[ ! "$line" =~ = ]]; then
            continue
        fi
        
        # Extract variable name (everything before first =)
        var_name="${line%%=*}"
        # Remove leading/trailing whitespace
        var_name=$(echo "$var_name" | xargs)
        
        if [[ -n "$var_name" ]]; then
            AI_ENV_VARS+=("$var_name")
        fi
    done < "$GLOBAL_ENV"
    
    # Only process variables that exist in BOTH local environment AND AI environment file
    for var_name in "${AI_ENV_VARS[@]}"; do
        # Check if this variable exists in the local environment (sourced above)
        var_value="${!var_name:-}"
        
        if [[ -n "$var_value" ]]; then
            log_info "🔍 Processing $var_name with value from local environment..."
            
            updated=false
            
            # First, try to match variable substitution patterns like ${VAR:-default}
            local var_subst_pattern="\\\${${var_name}:-[^}]*}"
            if grep -q "$var_subst_pattern" "$GLOBAL_ENV.tmp"; then
                # Replace the entire variable substitution with just the value
                # Add quotes if the value contains spaces
                local final_value="$var_value"
                if [[ "$var_value" =~ [[:space:]] ]]; then
                    final_value="\"$var_value\""
                fi
                local escaped_value=$(escape_sed "$final_value")
                if sed -i.tmp "s|$var_subst_pattern|$escaped_value|g" "$GLOBAL_ENV.tmp"; then
                    log_info "✅ Updated $var_name"
                    UPDATED_COUNT=$((UPDATED_COUNT + 1))
                    updated=true
                fi
            fi
            
            # If variable substitution didn't work, try traditional placeholder patterns
            if [[ "$updated" == false ]]; then
                for pattern in "${placeholder_patterns[@]}"; do
                    if grep -q "$pattern" "$GLOBAL_ENV.tmp"; then
                        if update_variable "$var_name" "$var_value" "$pattern"; then
                            UPDATED_COUNT=$((UPDATED_COUNT + 1))
                            updated=true
                            break
                        else
                            ERROR_COUNT=$((ERROR_COUNT + 1))
                            break
                        fi
                    fi
                done
            fi
            
            if [[ "$updated" == false ]]; then
                log_info "⚠️  No placeholder found for $var_name (value: ${var_value:0:20}...)"
            fi
        fi
    done
    
    # Replace the original with the updated version
    mv "$GLOBAL_ENV.tmp" "$GLOBAL_ENV"
    
    echo ""
    log_info "📊 Update Summary:"
    echo "  ✅ Successfully updated: $UPDATED_COUNT variables"
    if [[ $ERROR_COUNT -gt 0 ]]; then
        echo "  ❌ Errors encountered: $ERROR_COUNT"
    fi
    echo "  💾 Backup saved as: $GLOBAL_ENV.backup"
    echo "  📊 Updated file: $GLOBAL_ENV"
    
    echo ""
    log_info "🔍 You can verify with:"
    echo "  ai check"
    echo ""
    log_info "💡 Tip: If some variables weren't updated, check that your global .env"
    echo "   contains appropriate placeholder patterns for those variables."
    echo ""
    log_info "💡 Tip: Set LOCAL_ENV_FILE to use a different .env file:"
    echo "   LOCAL_ENV_FILE=.env.local ai env-sync"
}
