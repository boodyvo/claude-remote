# Claude Code Authentication Strategy

**Date:** February 5, 2026
**Decision:** Use Claude Pro/Max Subscription Authentication (NOT API Key)

---

## Overview

This project uses **Claude Pro/Max subscription authentication** instead of API key authentication for cost-effectiveness and simplicity.

## Why Subscription Over API Key

### Cost Benefits
- **Subscription:** Fixed monthly cost ($20 Pro / $200 Max) regardless of Claude Code usage
- **API:** Pay-per-token with potential for unexpected high bills
- **Result:** Predictable costs, no usage tracking needed

### Technical Benefits
- **Simpler setup:** Just `claude login` once on server
- **No API key management:** No secrets to rotate or store
- **Browser authentication:** Standard OAuth flow
- **Same account:** Use same credentials as claude.ai web

### Trade-offs
- **Context window:** 200K tokens (subscription) vs 1M tokens (API)
  - For our use case (voice commands), 200K is sufficient
- **Usage limits:** Subject to subscription fair use limits
  - For personal/small team use, limits are generous

---

## Implementation Details

### Setup Process

1. **On the Coolify/Hetzner server**, run once:
   ```bash
   claude login
   ```
   This will:
   - Open browser for authentication
   - Authenticate with your Pro/Max account
   - Store credentials in `~/.claude/` directory

2. **Verify authentication:**
   ```bash
   claude
   # Then in Claude prompt:
   /status
   ```
   Should show: "Account: Claude Pro" or "Claude Max"

3. **Important:** Do NOT set `ANTHROPIC_API_KEY` environment variable
   - If set, it overrides subscription and charges API costs
   - This is a common gotcha mentioned in Claude Code documentation

### Docker Considerations

Since we're using Docker containers:

**Option 1: Mount credentials from host (Recommended)**
```yaml
services:
  claudebox-web:
    volumes:
      - ${HOME}/.claude:/root/.claude:ro  # Read-only mount of host credentials
      - workspace:/workspace
```

**Option 2: Login inside container**
```bash
# One-time setup after deploying container
docker exec -it claudebox-web claude login
```

**We'll use Option 1** - mount host credentials to containers.

### Updated docker-compose.yml

**Remove these:**
```yaml
# ❌ DON'T DO THIS
environment:
  - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:?}
```

**Use this instead:**
```yaml
# ✅ DO THIS
volumes:
  - ${HOME}/.claude:/root/.claude:ro  # Mount subscription credentials
```

---

## Updated Environment Variables

### .env.example

**Before:**
```env
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**After:**
```env
# Claude Code Authentication
# This project uses Claude Pro/Max subscription via 'claude login' (NOT API key)
# IMPORTANT: Do NOT set ANTHROPIC_API_KEY environment variable
# Setup: Run 'claude login' once on the server
# Verify with: claude → /status
```

---

## Cost Impact

### Old Approach (API Key)
- API costs: Variable, pay-per-token
- Estimated: $20-50/month for moderate use
- Risk: Unexpected high bills during intensive sessions

### New Approach (Subscription)
- Subscription: $20/month (Pro) or $200/month (Max) - fixed
- Claude Code usage: $0 additional (included in subscription)
- **Total savings:** Potentially $20-50/month if usage is moderate

**Updated Total Monthly Cost:**
- VPS (Hetzner CPX21): €9 (~$9.50)
- Deepgram API: $25.80 (100 hours/month)
- Claude subscription: $20 (Pro) - **already have this**
- Domain: $1
- **Total: ~$36.30/month** (vs $66-96 with API key)

---

## Verification Checklist

After setup, verify:
- [ ] `claude` command works on server
- [ ] `/status` shows "Claude Pro" or "Claude Max" (not "API")
- [ ] `ANTHROPIC_API_KEY` is **NOT** set in environment
- [ ] `.env` file does **NOT** contain `ANTHROPIC_API_KEY`
- [ ] Docker containers can access `~/.claude/` credentials
- [ ] Voice commands execute without "API key missing" errors

---

## Troubleshooting

### Issue: "No API key found"

**Cause:** Claude Code can't find subscription credentials

**Solution:**
```bash
# On the server
claude login

# Verify
claude
/status
# Should show: "Account: Claude Pro" or "Claude Max"
```

### Issue: "Using API credits instead of subscription"

**Cause:** `ANTHROPIC_API_KEY` environment variable is set

**Solution:**
```bash
# Check environment
env | grep ANTHROPIC_API_KEY

# If found, unset it
unset ANTHROPIC_API_KEY

# Also remove from .env files
grep -r "ANTHROPIC_API_KEY" .

# Remove from Coolify environment variables UI
```

### Issue: Credentials not persisting in container

**Cause:** Volume mount not configured correctly

**Solution:**
```yaml
# In docker-compose.yml
volumes:
  - ${HOME}/.claude:/root/.claude:ro

# Or use absolute path
volumes:
  - /home/vlad/.claude:/root/.claude:ro
```

---

## Implementation Steps Updated

### Step 2: Obtain API Keys & Credentials

**Remove:** Anthropic API key acquisition

**Add:** Claude login verification
- Verify `claude login` is completed on Hetzner server
- Document the credentials location (`~/.claude/`)
- Test with `/status` command

### Step 3: Local Docker Compose Testing

**Update docker-compose.yml:**
- Remove `ANTHROPIC_API_KEY` environment variable
- Add volume mount: `- ${HOME}/.claude:/root/.claude:ro`

### Step 18: Coolify Deployment Configuration

**Remove:** ANTHROPIC_API_KEY from environment variables

**Add:** Note about credentials
- Ensure `claude login` is run on host before deployment
- Credentials at `/home/<user>/.claude/` will be mounted to containers

---

## References

- [Claude Code: Using with Pro/Max plan](https://support.claude.com/en/articles/11145838-using-claude-code-with-your-pro-or-max-plan)
- [Managing API key environment variables](https://support.claude.com/en/articles/12304248-managing-api-key-environment-variables-in-claude-code)
- [Switch from API key to subscription](https://codenote.net/en/posts/claude-code-anthropic-api-key-to-subscription/)

---

**Status:** Implemented
**Impact:** Reduces monthly costs by ~$20-50, simplifies authentication
**Next:** Update Step 2 and Step 3 implementation guides
