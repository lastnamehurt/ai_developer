#!/bin/bash

# AI Development Environment - Utility Functions
# This module contains common utility functions used across the AI dev tools

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

# Function to check if jq is available (needed for .cursor/rules.json manipulation)
check_jq() {
    if ! command -v jq >/dev/null 2>&1; then
        log_warning "jq not found - installing via homebrew for JSON processing"
        if command -v brew >/dev/null 2>&1; then
            brew install jq >/dev/null 2>&1 || log_warning "Failed to install jq - .cursor/rules.json updates may not work"
        else
            log_warning "homebrew not found - please install jq manually for .cursor/rules.json updates"
            return 1
        fi
    fi
    return 0
}

# Profile-aware helper functions
_load_env_once() {
  if [[ -f "$GLOBAL_ENV_FILE" ]]; then
    set -a
    source "$GLOBAL_ENV_FILE"
    set +a
  fi
}

# Helper function to merge MCP JSON files
_merge_mcp_json() {
  local output_file="$1"
  shift
  local input_files=("$@")
  
  if command -v jq >/dev/null 2>&1; then
    # Use jq for proper JSON merging
    jq -s 'reduce .[] as $it ({}; .mcpServers += ($it.mcpServers // {}))' "${input_files[@]}" > "$output_file"
  else
    # Fallback: simple concatenation (less reliable)
    echo '{"mcpServers":{}}' > "$output_file"
    for file in "${input_files[@]}"; do
      if [[ -f "$file" ]]; then
        # Simple merge - this is a basic fallback, jq is preferred
        python3 -c "
import json, sys
try:
    with open('$output_file', 'r') as f:
        result = json.load(f)
    with open('$file', 'r') as f:
        new_data = json.load(f)
    result['mcpServers'].update(new_data.get('mcpServers', {}))
    with open('$output_file', 'w') as f:
        json.dump(result, f, indent=2)
except Exception as e:
    sys.exit(1)
" 2>/dev/null || {
          log_warning "Failed to merge $file - jq and python3 not available"
        }
      fi
    done
  fi
}

_resolve_profile_cfg() {
  local profile="${1:-default}"
  local profile_cfg="$AI_PROFILES_DIR/${profile}.mcp.json"
  if [[ ! -f "$profile_cfg" ]]; then
    log_error "Profile not found: $profile_cfg"
    exit 1
  fi
  
  local out_cfg; out_cfg="$(mktemp).mcp.json"
  
  # Determine which base layers to include
  local base_layers=()
  local layers_dir="$CONFIG_DIR/mcp-layers"
  
  # Check for template layers if global layers don't exist
  if [[ ! -d "$layers_dir" ]]; then
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    layers_dir="$script_dir/../templates/mcp-layers"
  fi
  
  # All profiles get common base
  if [[ -f "$layers_dir/base.common.json" ]]; then
    base_layers+=("$layers_dir/base.common.json")
  fi
  
  # Add conversational layer for most profiles
  if [[ "$profile" != "default" && -f "$layers_dir/base.conversational.json" ]]; then
    base_layers+=("$layers_dir/base.conversational.json")
  fi
  
  # Add persistent layer for memory-enabled profiles
  if [[ "$profile" == "persistent" || "$profile" == "research" ]] && [[ -f "$layers_dir/base.persistent.json" ]]; then
    base_layers+=("$layers_dir/base.persistent.json")
  fi
  
  # Merge base layers with profile-specific config
  base_layers+=("$profile_cfg")
  _merge_mcp_json "$out_cfg" "${base_layers[@]}"
  
  # Apply environment variable substitution
  if command -v envsubst >/dev/null 2>&1; then
    local tmp="${out_cfg}.tmp"
    envsubst < "$out_cfg" > "$tmp" && mv "$tmp" "$out_cfg"
  elif command -v sed >/dev/null 2>&1; then
    # Fallback: basic sed replacement for common patterns
    local tmp="${out_cfg}.tmp"
    cp "$out_cfg" "$tmp"
    # Replace ${VAR:-default} patterns
    sed -i.bak "s/\${HOME}/$(echo "$HOME" | sed 's/\//\\\//g')/g" "$tmp" 2>/dev/null || true
    sed -i.bak "s/\${KUBECONFIG:-\${HOME}\/.kube\/config}/$(echo "${KUBECONFIG:-${HOME}/.kube/config}" | sed 's/\//\\\//g')/g" "$tmp" 2>/dev/null || true
    sed -i.bak "s/\${MEMORY_BANK_ROOT:-\${HOME}\/.local\/ai-dev\/memory-banks}/$(echo "${MEMORY_BANK_ROOT:-${HOME}/.local/ai-dev/memory-banks}" | sed 's/\//\\\//g')/g" "$tmp" 2>/dev/null || true
    # Replace other environment variables
    for var in GITLAB_PERSONAL_ACCESS_TOKEN GITLAB_API_URL GITLAB_READ_ONLY_MODE USE_GITLAB_WIKI USE_MILESTONE USE_PIPELINE; do
      if [[ -n "${!var:-}" ]]; then
        sed -i.bak "s/\${$var}/$(echo "${!var}" | sed 's/\//\\\//g')/g" "$tmp" 2>/dev/null || true
      fi
    done
    mv "$tmp" "$out_cfg"
    rm -f "${tmp}.bak" 2>/dev/null || true
  fi
  
  printf "%s" "$out_cfg"
}

_require_env() {
  # If no arguments provided, return success (nothing to check)
  if [[ $# -eq 0 ]]; then
    return 0
  fi
  
  local profile="${1:-}"
  local missing=()
  local required_vars=()
  
  # If first argument is not a profile name, treat all arguments as variable names
  if [[ "$profile" =~ ^[A-Z_][A-Z0-9_]*$ ]]; then
    # Old behavior: all arguments are variable names
    required_vars=("$@")
    profile=""
  else
    # New behavior: first argument is profile, rest are variable names
    shift
    required_vars=("$@")
    
    # Add profile-specific requirements
    case "$profile" in
      "devops")
        required_vars+=("GITLAB_PERSONAL_ACCESS_TOKEN" "KUBECONFIG")
        ;;
      "qa")
        required_vars+=("GITLAB_PERSONAL_ACCESS_TOKEN")
        ;;
      "research")
        # Optional: MEMORY_BANK_ROOT (has default)
        ;;
      "persistent")
        # Optional: MEMORY_BANK_ROOT (has default)
        ;;
    esac
  fi
  
  # Check each required variable
  if [[ ${#required_vars[@]} -eq 0 ]]; then
    return 0
  fi
  
  for k in "${required_vars[@]}"; do 
    [[ -n "${!k:-}" ]] || missing+=("$k")
  done
  
  if (( ${#missing[@]} )); then
    if [[ -n "$profile" ]]; then
      log_error "Profile '$profile' missing vars in $GLOBAL_ENV_FILE: ${missing[*]}"
    else
      log_error "Missing vars in $GLOBAL_ENV_FILE: ${missing[*]}"
    fi
    return 1
  fi
  return 0
}

# Check required dependencies
check_deps() {
  local deps=(jq git-mcp-server k8s-mcp-server uvx npx)
  local missing=()
  
  for cmd in "${deps[@]}"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      missing+=("$cmd")
    fi
  done
  
  if (( ${#missing[@]} )); then
    log_error "Missing dependencies: ${missing[*]}"
    log_info "Install missing dependencies:"
    for dep in "${missing[@]}"; do
      case "$dep" in
        "jq")
          echo "  • jq: brew install jq"
          ;;
        "git-mcp-server")
          echo "  • git-mcp-server: npm install -g @modelcontextprotocol/git-server"
          ;;
        "k8s-mcp-server")
          echo "  • k8s-mcp-server: go install github.com/stablecog/mcp-k8s@latest"
          ;;
        "uvx")
          echo "  • uvx: pip install uv"
          ;;
        "npx")
          echo "  • npx: install Node.js and npm"
          ;;
        *)
          echo "  • $dep: please install manually"
          ;;
      esac
    done
    return 1
  fi
  
  log_success "All dependencies available"
  return 0
}

# Load environment variables from a file
load_env_from_file() {
    local env_file="$1"
    local file_label="$2"
    local loaded_count=0
    
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment variables from $file_label"
        
        # Read and export variables, skipping comments and empty lines
        while IFS= read -r line || [[ -n "$line" ]]; do
            # Skip comments and empty lines
            if [[ "$line" =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
                continue
            fi
            
            # Check if line contains an assignment
            if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
                var_name="${BASH_REMATCH[1]}"
                var_value="${BASH_REMATCH[2]}"
                
                # Remove surrounding quotes if present
                if [[ "$var_value" =~ ^\"(.*)\"$ ]] || [[ "$var_value" =~ ^\'(.*)\'$ ]]; then
                    var_value="${BASH_REMATCH[1]}"
                fi
                
                # Export the variable
                export "$var_name"="$var_value"
                ((loaded_count++))
            fi
        done < "$env_file"
        
        if [[ $loaded_count -gt 0 ]]; then
            log_success "Loaded $loaded_count environment variables from $file_label"
        fi
    fi
    
    return 0
}

# Find templates directory
find_templates_dir() {
    # Try multiple possible locations for templates directory
    local possible_templates=(
        "$CONFIG_DIR/templates"
        "./templates"
        "../templates"
        "templates"
    )
    
    # First check if templates directory exists and has engineering-workflow.md
    for dir in "${possible_templates[@]}"; do
        if [[ -d "$dir" && -f "$dir/engineering-workflow.md" ]]; then
            echo "$dir"
            return 0
        fi
    done
    
    # If not found in templates, check docs directory
    local possible_docs=(
        "$CONFIG_DIR/docs"
        "./docs"
        "../docs"
        "docs"
    )
    
    for dir in "${possible_docs[@]}"; do
        if [[ -d "$dir" && -f "$dir/engineering-workflow.md" ]]; then
            echo "$dir"
            return 0
        fi
    done
    
    return 1
}

# Find install script
find_install_script() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    POSSIBLE_PATHS=(
        # Primary location - unified under ~/.local/ai-dev
        "$HOME/.local/ai-dev/install.sh"
        # If running from project directory
        "./install.sh"
        # If script is in project bin/ directory
        "$script_dir/../install.sh"
        # Legacy locations (fallback)
        "$HOME/.local/ai-dev/install.sh"
        "${XDG_CONFIG_HOME:-$HOME/.config}/ai-dev/install.sh"
        # GitHub or git clone locations
        "$HOME/ai-dev/install.sh"
        "$HOME/workspace/ai-dev/install.sh"
        "$HOME/workspace/local_dev/ai-dev/install.sh"
    )
    
    for path in "${POSSIBLE_PATHS[@]}"; do
        if [[ -f "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    return 1
}
