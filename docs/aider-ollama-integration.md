# Aider & Ollama Integration Guide

Leverage **Aider** (AI pair programming) and **Ollama** (local LLMs) for a powerful, cost-effective, and private development workflow that complements your IDE-based tools.

## 🎯 Why Aider + Ollama?

### **Aider** - Terminal-First AI Pair Programming

**Fills workflow gaps:**
- While Cursor and Claude Code are IDE-focused, Aider excels at command-line workflows
- Perfect for quick edits, refactoring across multiple files, and CI/CD integration
- Better git integration with automatic commits and feature branch awareness

**Model flexibility:**
- Supports multiple providers (OpenAI, Anthropic, local models via Ollama)
- Cost optimization by using different models for different tasks
- Collaborative editing across multiple files simultaneously

### **Ollama** - Local LLM Powerhouse

**Privacy and offline work:**
- Run models like Llama, CodeLlama, or DeepSeek locally
- No code sent to external APIs - perfect for proprietary code
- Work completely offline when needed

**Cost control:**
- No API costs for unlimited usage
- Great for experimentation and high-volume tasks
- Custom fine-tuning on your codebase

**Integration benefits:**
- Use with Aider for fully local coding assistant
- Complement commercial tools (Cursor/Claude) for sensitive code
- Quick queries and experimentation without API limits

## 🚀 Quick Setup

### Install Aider

```bash
pip install aider-chat
```

Or use the included installer:
```bash
./install.sh  # Installs Aider automatically
```

### Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or use included installer
./install.sh
```

### Pull Models

```bash
# Popular coding models
ollama pull codellama      # Best for code generation
ollama pull llama3.1       # General purpose
ollama pull deepseek-coder # Strong code understanding
```

## 📋 Using Aider with aidev

### Basic Usage

**Using aidev's `ai aider` command (recommended):**

```bash
# Launch Aider with aider profile (default)
ai aider

# Use specific model
ai aider --model claude-sonnet-4-5
ai aider --model ollama/codellama

# Auto-accept changes
ai aider --yes

# Use different profile
ai aider --profile web

# Combine options
ai aider --model ollama/codellama --yes
```

**Direct Aider usage (still supported):**

```bash
# Use Aider with your active profile's environment
ai use aider
aider --model claude-sonnet-4-5

# Or use with any profile
ai use web
export ANTHROPIC_API_KEY=$(ai env get ANTHROPIC_API_KEY)
aider --model claude-sonnet-4-5 --yes  # Auto-accept changes
```

### Aider Profile

aidev includes an Aider-optimized profile:

```bash
# Switch to Aider profile
ai use aider

# Launch Aider using aidev command (recommended)
ai aider --model claude-sonnet-4-5

# Or launch directly
aider --model claude-sonnet-4-5
```

**Note:** The `ai aider` command automatically uses the `aider` profile by default, so you don't need to switch profiles first.

**Profile features:**
- Auto-commits enabled (`AIDER_AUTO_COMMITS=true`)
- Git integration configured
- Filesystem and git MCP servers enabled
- Memory bank for context persistence

### Environment Variables

Aider respects aidev's environment management:

```bash
# Set API keys (automatically available to Aider)
ai env set ANTHROPIC_API_KEY sk-ant-xxx
ai env set OPENAI_API_KEY sk-openai-xxx

# Aider will use these automatically
aider --model claude-sonnet-4-5
```

## 🔧 Using Ollama with aidev

### Code Review with Ollama

```bash
# Review staged files using Ollama
ai review --staged --provider ollama

# Review specific files
ai review file1.py file2.py --provider ollama

# Custom model and prompt
# Edit ~/.aidev/review.json:
{
  "provider": "ollama",
  "ollama_model": "codellama",
  "ollama_prompt": "Review this code for bugs, performance issues, and best practices"
}
```

### Workflows with Ollama

Ollama is available as a workflow assistant:

```bash
# Run workflow with Ollama fallback
ai workflow doc_improver README.md

# Ollama is automatically used if other assistants unavailable
# Or explicitly use Ollama:
ai workflow doc_improver README.md --tool ollama
```

### Direct Ollama Command

```bash
# Launch Ollama directly
ai ollama

# Or use Ollama CLI directly
ollama run codellama "Explain this Python function..."
```

## 💡 Practical Workflows

### Local-First Development

**Use Ollama + Aider for:**
- Proprietary code that can't leave your machine
- High-volume refactoring tasks
- Experimentation without API costs
- Offline development

**Use Commercial Tools (Cursor/Claude) for:**
- Complex architecture decisions
- Deep codebase understanding
- Production-critical changes

### Hybrid Approach

```bash
# Morning: Use Ollama + Aider for quick fixes
ai aider --model ollama/codellama

# Afternoon: Use Claude for complex features
ai use web
ai claude

# Or use Aider with Claude for complex features
ai aider --model claude-sonnet-4-5

# Evening: Use Ollama for code review
ai review --all --provider ollama
```

### Cost Optimization

```bash
# Use Ollama for routine tasks
ai aider --model ollama/codellama
# Then in Aider: "Refactor this function"

# Use Claude for complex tasks
ai aider --model claude-sonnet-4-5
# Then in Aider: "Design a new authentication system"
```

### Workflow Integration

aidev includes workflows that leverage Aider:

```bash
# Implement code changes from a ticket using Aider
ai workflow implement_with_aider "Add user authentication"

# Quick refactoring with local Ollama model
ai workflow quick_refactor "Refactor UserService class"
```

## 🎨 Aider Profile Configuration

The built-in Aider profile (`examples/profiles/aider.json`) includes:

```json
{
  "name": "aider",
  "description": "AI pair programming with Aider CLI",
  "extends": "default",
  "tags": ["cli", "pair-programming", "git", "terminal"],
  "mcp_servers": [
    {"name": "filesystem", "enabled": true},
    {"name": "git", "enabled": true},
    {"name": "github", "enabled": true},
    {"name": "memory-bank", "enabled": true}
  ],
  "environment": {
    "AIDER_AUTO_COMMITS": "true",
    "AIDER_DARK_MODE": "true",
    "AIDER_GITIGNORE": "true"
  }
}
```

### Custom Aider Profile

Create your own Aider profile:

```bash
# Clone the aider profile
ai profile clone aider my-aider

# Edit ~/.aidev/config/profiles/custom/my-aider.json
# Add custom environment variables, MCP servers, etc.
```

## 🔄 Workflow Integration

### Aider in Workflows

You can use Aider as an external reviewer in workflows:

```yaml
# .aidev/workflows.yaml
my_workflow:
  steps:
    - name: code_review
      profile: pair-programmer
      prompt: code_reviewer
      # Aider can be invoked via external review config
```

### Ollama in Workflows

Ollama is available as a workflow assistant:

```bash
# Ollama is in the fallback chain
# claude → codex → cursor → gemini → ollama

# Or use explicitly
ai workflow my_workflow --tool ollama
```

## 📊 Comparison: When to Use What

| Tool | Best For | Cost | Privacy |
|------|----------|------|---------|
| **Aider + Ollama** | Quick edits, refactoring, proprietary code, offline work | Free (local) | High |
| **Aider + Claude** | Complex features, architecture, production code | ~$10/month | Medium |
| **Cursor** | IDE integration, visual editing, large codebases | Paid | Medium |
| **Claude Code** | Deep understanding, complex reasoning | Paid | Medium |

## 🛠️ Advanced Configuration

### Custom Ollama Models

```bash
# Pull specialized models
ollama pull codellama:13b        # Larger, more capable
ollama pull deepseek-coder:6.7b  # Fast and efficient

# Use in Aider
aider --model ollama/codellama:13b
```

### Aider Configuration

Create `~/.aider.conf`:

```yaml
# Aider configuration
model: ollama/codellama
auto_commits: true
dark_mode: true
gitignore: true
```

### Review Configuration

Edit `~/.aidev/review.json`:

```json
{
  "provider": "ollama",
  "ollama_model": "codellama",
  "ollama_prompt": "Review this code for:\n1. Bugs and errors\n2. Performance issues\n3. Best practices\n4. Security concerns"
}
```

## 🚨 Troubleshooting

### Aider Not Found

```bash
# Install Aider
pip install aider-chat

# Verify installation
which aider
aider --version
```

### Ollama Not Found

```bash
# Install Ollama
brew install ollama  # macOS
# or
curl -fsSL https://ollama.com/install.sh | sh  # Linux

# Verify installation
which ollama
ollama --version
```

### Model Not Found

```bash
# Pull the model first
ollama pull codellama

# Verify model is available
ollama list
```

### Environment Variables Not Loading

```bash
# Ensure variables are set
ai env list

# Export manually if needed
export ANTHROPIC_API_KEY=$(ai env get ANTHROPIC_API_KEY)
```

## 📚 Learn More

- **Aider**: https://aider.chat
- **Ollama**: https://ollama.com
- **aidev Profiles**: [Profile Guide](profiles.md)
- **Workflows**: [Workflow Guide](workflows.md)

## 🎯 Next Steps

1. **Install both tools**: `./install.sh` or manual installation
2. **Try Aider**: `ai use aider && aider --model claude-sonnet-4-5`
3. **Try Ollama review**: `ai review --staged --provider ollama`
4. **Create custom profile**: `ai profile clone aider my-local-dev`
5. **Experiment**: Find your optimal workflow combining local and cloud tools

---

**Pro Tip**: Use Ollama + Aider for your daily development loop, and switch to Claude/Cursor when you need deeper reasoning or IDE integration. This gives you the best of both worlds: cost-effective local tools and powerful cloud-based assistance when needed.
