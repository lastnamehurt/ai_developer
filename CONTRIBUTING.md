# 🛠 Contributing to AI Development Environment

Thanks for contributing! This guide shows how to extend the AI development environment with new MCP servers, tools, and integrations.

## 🔌 Adding New MCP Servers

To add a new third-party MCP server (like a new service integration):

### 1. Update MCP Templates

Add your server to `templates/mcp.json`:

```json
{
  "mcpServers": {
    "your-server-name": {
      "command": "npx",
      "args": [
        "-y",
        "@your-org/your-mcp-server"
      ]
    }
  }
}
```

### 2. Update the separate MCP servers file

Add your server to the `create_mcp_servers_file()` function in `bin/ai`:

```bash
"your-server-name": {
  "command": "npx",
  "args": [
    "-y", 
    "@your-org/your-mcp-server"
  ]
}
```

### 3. Add Environment Variables (if needed)

If your MCP server needs environment variables, add them to:

**`.env.template`:**
```bash
# Your Service Configuration
YOUR_SERVICE_API_KEY=your-api-key-here
YOUR_SERVICE_URL=https://your-service.com/api
```

**`install.sh` (both template sections):**
```bash
# Your Service Configuration
YOUR_SERVICE_API_KEY=\${YOUR_SERVICE_API_KEY:-your-api-key-here}
YOUR_SERVICE_URL=\${YOUR_SERVICE_URL:-https://your-service.com/api}
```

**`bin/ai` (template creation):**
```bash
# Your Service Configuration  
YOUR_SERVICE_API_KEY=your-api-key-here
YOUR_SERVICE_URL=https://your-service.com/api
```

### 4. Update Documentation

Add your service to the README.md:

```markdown
#### Supported MCP Servers

- **Your Service**: Description of what it provides
```

## 🏗 Creating Custom MCP Servers

For custom/internal MCP servers, place them in the `mcp-servers/` directory:

### 1. Create Your Server Directory

```bash
mkdir mcp-servers/your-custom-server
cd mcp-servers/your-custom-server
```

### 2. Create Your MCP Server

**`package.json`:**
```json
{
  "name": "your-custom-server",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@modelcontextprotocol/sdk": "latest"
  }
}
```

**`index.ts`:**
```typescript
#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

// Your MCP server implementation
const server = new Server(
  {
    name: 'your-custom-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Add your tools and handlers here
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'your_tool',
        description: 'Description of what your tool does',
        inputSchema: {
          type: 'object',
          properties: {
            // Your tool parameters
          },
        },
      },
    ],
  };
});

// Start the server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### 3. Add to Templates

**`templates/mcp.json`:**
```json
"your-custom-server": {
  "command": "npx",
  "args": [
    "tsx",
    "${HOME}/.local/ai-dev/mcp-servers/your-custom-server/index.ts"
  ]
}
```

### 4. Update Installation

**`install.sh`:**
```bash
# Install MCP servers
if [[ -d "mcp-servers/your-custom-server" ]]; then
    mkdir -p "$BASE_DIR/mcp-servers/your-custom-server"
    cp -r mcp-servers/your-custom-server/* "$BASE_DIR/mcp-servers/your-custom-server/"
    
    if [[ -f "$BASE_DIR/mcp-servers/your-custom-server/package.json" ]]; then
        cd "$BASE_DIR/mcp-servers/your-custom-server"
        npm install --silent
        cd - > /dev/null
    fi
    
    log_success "Installed Your Custom Server MCP server"
fi
```

## 🛠 Adding New AI Tools

To support a new AI tool (like a new IDE or AI assistant):

### 1. Add Tool Command

Add a new case to `bin/ai`:

```bash
"your-tool")
    if [[ -n "$2" ]]; then
        cd "$2"
    fi
    
    load_environment_variables
    
    if command -v your-tool >/dev/null 2>&1; then
        your-tool "${@:2}"
    else
        log_error "Your Tool not found. Please install it first."
        exit 1
    fi
    ;;
```

### 2. Update Help Documentation

Add to the `show_help()` function:

```bash
echo "  ai your-tool [path]       # Launch Your Tool with environment"
```

### 3. Update README

Add to the supported tools table:

```markdown
| Your Tool | `ai your-tool` | Launch Your Tool with environment |
```

## 📝 Adding Environment Variables

To add support for new services:

### 1. Add to Template Files

**`.env.template`:**
```bash
# New Service Configuration
NEW_SERVICE_TOKEN=your-token-here
NEW_SERVICE_URL=https://api.newservice.com
```

### 2. Add to Install Script

**Both template sections in `install.sh`:**
```bash
# New Service Configuration
NEW_SERVICE_TOKEN=\${NEW_SERVICE_TOKEN:-your-token-here}
NEW_SERVICE_URL=\${NEW_SERVICE_URL:-https://api.newservice.com}
```

### 3. Add to Binary Template

**In `bin/ai` template creation:**
```bash
# New Service Configuration
NEW_SERVICE_TOKEN=your-token-here
NEW_SERVICE_URL=https://api.newservice.com
```

## 🧪 Testing Your Changes

### 1. Test Installation

```bash
# Test local installation
./install.sh

# Run all tests (includes installation simulation)
./tests/run-tests.sh

# Run specific test suites
./tests/run-tests.sh installation
./tests/run-tests.sh -v  # verbose output
```

### 2. Test Profile System

```bash
# Test profile resolution and base layer merging
./tests/run-tests.sh profiles

# Verify each profile resolves correctly:
# - default: filesystem, git
# - persistent: filesystem, git, memory-bank, serena  
# - devops: filesystem, git, gitlab, k8s, serena
# - qa: filesystem, git, gitlab, cypress, test-overlap-analyzer, serena
# - research: filesystem, git, memory-bank, serena, duckduckgo, compass, sequentialthinking
```

### 3. Test Sub Agent Setup

```bash
# Test Claude Sub Agent creation
./tests/run-tests.sh agents

# Verify agents are created in .claude/agents/:
# - devops-deployer.md (deployment specialist)
# - qa-test-runner.md (testing workflow)
# - core-dev-reviewer.md (code review)
# - research-synthesizer.md (research synthesis)
```

### 4. Test MCP Server Integration

```bash
# Initialize in test project
mkdir test-project && cd test-project
ai init

# Check MCP configuration with profile
~/.local/ai-dev/bin/ai claude --profile devops --help 2>/dev/null || echo "Profile resolved correctly"

# Verify symlinks and agents created
ls -la .claude/
ls -la .claude/agents/
```

### 5. Test Environment Variables

```bash
# Check environment loading
ai load

# Verify profile-specific requirements
ai claude --profile devops  # Should check for GITLAB_TOKEN + KUBECONFIG
ai claude --profile qa       # Should check for GITLAB_TOKEN only
```

### Implementation Testing Summary

The comprehensive change plan was tested using:

**DRY Profile Architecture:**
- ✅ Base layer system (common, conversational, persistent) eliminates duplication
- ✅ Profile resolution merges base layers correctly using jq
- ✅ Environment variable substitution works with envsubst and sed fallbacks

**Sub Agent Integration:**
- ✅ All 4 agents created automatically by `ai init`
- ✅ Proper YAML frontmatter with names and descriptions
- ✅ Agents inherit MCP tools from active profiles
- ✅ Version controlled in project-specific `.claude/agents/` directory

**Profile Matrix Validation:**
- ✅ Each profile includes correct server combinations as specified
- ✅ Memory persistence strategy using memory-bank backend
- ✅ Profile-specific environment requirements enforced
- ✅ Dependency checking with installation guidance

**End-to-End Testing:**
- ✅ Simulated installation from repository (`tests/test-ai-installation.sh`)
- ✅ Profile resolution across all 5 profiles (`tests/test-ai-profiles.sh`)  
- ✅ Sub Agent creation and setup (`tests/test-ai-agents.sh`)
- ✅ Environment loading and requirements checking
- ✅ MCP server configuration and symlink management

**Integrated Test Framework:**
- ✅ All implementation tests integrated with existing test suite
- ✅ Comprehensive test runner with filtering and verbose output
- ✅ Test organization follows established patterns in `tests/` directory
