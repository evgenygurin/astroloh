# Claude Code CLI Tools

This directory contains CLI tools for working with Claude AI.

## Files

### 🟢 `claude_code_cli_simple.py` - **WORKING**

A simplified Claude CLI client that works without MCP dependencies.

**Features:**

- Direct Claude API integration with latest Sonnet 4 model
- Interactive chat mode
- Conversation history management
- Robust API key validation
- Proper type safety with MessageParam
- No dependency issues

**Usage:**

```bash
# Interactive mode
uv run claude_code_cli_simple.py

# Single query mode
uv run claude_code_cli_simple.py "What is this project about?"
```

**Setup:**

1. Add your Anthropic API key to `.env`:

   ```
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

### 🔴 `claude_code_cli.py` - **BROKEN**

Original MCP-based CLI with compatibility issues.

**Issue:**

```
ImportError: cannot import name 'eval_type_backport' from 'pydantic._internal._typing_extra'
```

**Cause:** Version incompatibility between:

- `mcp==1.12.4`
- `pydantic==2.11.7`

The MCP package expects an older Pydantic internal API that no longer exists.

## Problem Summary

The MCP (Model Context Protocol) package has a dependency issue with newer versions of Pydantic. The package tries to import `eval_type_backport` from Pydantic's internal modules, but this function was removed in newer Pydantic versions.

## Solution

Use `claude_code_cli_simple.py` instead, which:

1. ✅ Works without MCP dependencies
2. ✅ Uses direct Anthropic API calls
3. ✅ Has proper error handling
4. ✅ Supports both interactive and single-query modes
5. ✅ Includes conversation history management

## Commands

```bash
# Install dependencies (already done in project)
uv add anthropic python-dotenv

# Run the working CLI
uv run claude_code_cli_simple.py

# Interactive commands in the CLI:
# - 'quit' - Exit the program
# - 'clear' - Clear conversation history  
# - 'history' - Show conversation history
# - Any other text - Send as query to Claude
```

## Environment Variables

Add to your `.env` file:

```bash
# Required for Claude API access
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Notes

- The simple version maintains conversation context across queries
- Conversation history is limited to the last 10 messages to avoid token limits
- The script includes proper error handling for missing API keys
- All Claude API calls use the latest `claude-sonnet-4-20250514` model
- Enhanced API key validation (checks for proper sk-ant- prefix and length)
- Improved type safety with proper MessageParam usage
