# Claude CLI Setup Guide

## Installation

Claude CLI is installed via npm:
```bash
npm install -g @anthropic-ai/claude-code
```

**Version:** 2.1.34 (as of Feb 2026)

## Authentication

### macOS Issue
On macOS, Claude stores OAuth credentials in **Keychain**, not in files. This breaks Docker container workflows.

### Solution
Extract credentials from Keychain to file:

```bash
# Extract from macOS Keychain
security find-generic-password -s "Claude Code-credentials" -w > .claude/.credentials.json
```

**Important:**
- File MUST be named `.credentials.json` (with leading dot)
- File location: `~/.claude/.credentials.json` or project `.claude/.credentials.json`
- Never commit this file (add to `.gitignore`)

## Command Line Usage

### Basic Usage
```bash
claude -p "prompt text" --output-format text
```

### Stream JSON Format (for programmatic use)
```bash
claude -p "prompt text" --output-format stream-json --verbose
```

**Output:** Line-by-line JSON events
- `{"type":"system","subtype":"init",...}` - Initialization
- `{"type":"assistant","message":{...}}` - Response with text
- `{"type":"result",...}` - Final result with cost/usage

### Key Flags
- `-p "text"` - Prompt (required)
- `--output-format` - `text`, `json`, or `stream-json`
- `--verbose` - Required for stream-json with `-p`
- `--max-turns N` - Limit conversation turns
- `--resume SESSION_ID` - Resume existing session
- `-w /path` - Working directory (use `docker exec -w` instead)

## Docker Integration

### Container Setup
```yaml
services:
  bot:
    image: python:3.11-slim
    volumes:
      - ./.claude:/root/.claude  # Mount credentials
    command: |
      bash -c "
        apt-get update && apt-get install -y nodejs npm &&
        npm install -g @anthropic-ai/claude-code &&
        # your app
      "
```

### Testing
```bash
# Test authentication
docker exec container-name claude -p "What is 2+2?" --output-format text

# Expected: "4"
# If you see "Not logged in", check .credentials.json
```

## Stream JSON Response Format

Example response for "What is 2+2?":

```json
{"type":"system","subtype":"init","session_id":"8b4872d5...","model":"claude-opus-4-6","tools":[...],"claude_code_version":"2.1.34"}
{"type":"assistant","message":{"content":[{"type":"text","text":"4"}],"usage":{"input_tokens":3,"output_tokens":1}}}
{"type":"result","subtype":"success","result":"4","total_cost_usd":0.029409,"session_id":"8b4872d5..."}
```

### Key Fields for Parsing
- `session_id` - For resuming conversations
- `message.content[].text` - The actual response text
- `result.total_cost_usd` - Cost tracking
- `usage.input_tokens` / `output_tokens` - Token usage
- `stop_reason` - Why generation stopped

## Cost Information

From test: "What is 2+2?"
- Input tokens: 3
- Output tokens: 1 (just "4")
- Cache read: 15,289 tokens
- Cache creation: 3,460 tokens
- **Cost: $0.029** (~3 cents for simple query)

Model: `claude-opus-4-6` (200K context window)

## Common Issues

### "Not logged in"
- Ensure `.credentials.json` exists (not `credentials.json`)
- Check file has content (~539 bytes JSON)
- Re-extract from Keychain if credentials expired

### "Error: EROFS: read-only file system"
- Remove `:ro` from Docker volume mount
- Claude CLI needs to write to `~/.claude/` directory

### "unknown option --workspace"
- No --workspace flag exists
- Use `docker exec -w /path` instead

### "requires --verbose"
- When using `-p` with `--output-format stream-json`, add `--verbose`

## Security Best Practices

1. **Never commit credentials**
   - Add `.claude/` and `*.credentials.json` to `.gitignore`

2. **Use project-local `.claude` directory**
   - Don't modify system `~/.claude` directory
   - Keep project credentials isolated

3. **Rotate credentials regularly**
   - OAuth tokens can expire
   - Re-run security command to refresh

4. **Restrict file permissions**
   - `chmod 700 .claude/`
   - `chmod 600 .claude/.credentials.json`

## References

- Issue: https://github.com/anthropics/claude-code/issues/10039
- Docs: https://code.claude.com/docs/en/authentication
