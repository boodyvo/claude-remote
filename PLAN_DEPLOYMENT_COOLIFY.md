# Coolify Deployment Plan - Complete Guide

## 📋 Overview

This document provides a complete deployment plan for Claude Remote Runner on Coolify, including:
- **Manual deployment** (UI-based, step-by-step)
- **One-command deployment** (API/webhook automation)
- **CI/CD automation** (GitHub Actions)

---

## 🎯 Deployment Options

### Option 1: Manual UI Deployment (Recommended for First Time)
**Time:** 15-20 minutes
**Difficulty:** Easy
**Best for:** First deployment, learning the system

### Option 2: One-Command Deployment
**Time:** 2-3 minutes
**Difficulty:** Medium
**Best for:** Quick redeployment, automation

### Option 3: GitHub Actions CI/CD
**Time:** 10 minutes setup, then automatic
**Difficulty:** Advanced
**Best for:** Continuous deployment on every push

---

## 📝 Prerequisites (All Options)

### 1. Server & Coolify Setup
- [ ] Hetzner VPS (CPX21 or similar) provisioned
- [ ] Ubuntu 24.04 LTS installed
- [ ] Coolify installed and running
- [ ] SSH access configured

### 2. Domain Configuration
- [ ] Domain name available (e.g., claude.yourdomain.com)
- [ ] DNS A record created pointing to server IP
- [ ] DNS propagated (verify with `dig claude.yourdomain.com`)

### 3. Claude Authentication & API Keys
- [ ] Claude Pro/Max subscription active
- [ ] Run `claude login` on server (authenticate with subscription)
- [ ] Telegram bot token (from @BotFather)
- [ ] Deepgram API key (from deepgram.com)
- [ ] Your Telegram user ID (from @userinfobot)

### 4. Repository Access
- [ ] GitHub repository created/forked
- [ ] Repository contains all project files
- [ ] Repository is public OR SSH key configured in Coolify

---

## 🚀 Option 1: Manual UI Deployment

### Step 1: Access Coolify Dashboard

```bash
# Open Coolify in browser
https://your-server-ip:8000
# OR if custom domain configured
https://coolify.yourdomain.com
```

### Step 2: Create New Project

**Navigation:** Dashboard → Projects → **+ New Project**

**Configuration:**
```
Project Name: Claude Remote Runner
Description: Voice-controlled Claude Code with Telegram bot
Environment: production
```

Click **Create**

### Step 3: Add Git Repository Resource

**Navigation:** Project Overview → **+ New Resource** → **Docker Compose**

**Select:** Git Repository

**Repository Configuration:**
```
Git Provider: GitHub
Repository URL: https://github.com/yourusername/claude-remote-runner.git
Branch: main
Auto Deploy: ✓ Enabled
Docker Compose Location: /docker-compose.yml
```

Click **Continue**

### Step 4: Configure Environment Variables

**Navigation:** Resource → **Environment Variables** tab → **+ Add**

**Important - Claude Authentication:**
Before adding environment variables, SSH to server and run:
```bash
claude login
```
Follow browser auth flow, then verify with `claude` → `/status`

**Required Variables:**

```env
TELEGRAM_TOKEN=1234567890:ABC...
  ☑ Secret

DEEPGRAM_API_KEY=...
  ☑ Secret

WEBHOOK_URL=https://claude.yourdomain.com/${TELEGRAM_TOKEN}
  ☐ Secret (contains variable reference)

ALLOWED_USER_IDS=123456789
  ☐ Secret
```

**Note:** Do NOT add ANTHROPIC_API_KEY - using Claude subscription instead

**Optional Variables:**

```env
BASIC_AUTH_USER=admin
  ☐ Secret

BASIC_AUTH_PASS=your-secure-password
  ☑ Secret
```

Click **Save** after each variable

### Step 5: Configure Domain & SSL

**Navigation:** Resource → **Domains** tab → **+ Add Domain**

**Configuration:**
```
Domain: claude.yourdomain.com
HTTPS: ✓ Enabled
Auto SSL: ✓ Let's Encrypt
Force HTTPS: ✓ Enabled
```

Click **Save**

**Verify DNS:**
```bash
dig claude.yourdomain.com +short
# Should return: your-server-ip
```

### Step 6: Configure Services

**Navigation:** Resource → **Configuration** tab

Coolify auto-detects services from docker-compose.yml:

**claudebox-web:**
- Internal Port: 3000
- Domain: claude.yourdomain.com
- Path: /

**telegram-bot:**
- Internal Port: 8443
- Domain: claude.yourdomain.com
- Path: /${TELEGRAM_TOKEN}

Click **Save**

### Step 7: Deploy

**Navigation:** Resource → Top right → **Deploy** button

Click **Deploy Now**

**Monitor deployment:**
- Watch logs in real-time
- Wait for "Deployment successful" message (2-5 minutes)
- Verify both services show green "healthy" status

### Step 8: Configure Telegram Webhook

```bash
# Replace <TOKEN> with your actual Telegram bot token
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://claude.yourdomain.com/<TOKEN>" \
  -d "allowed_updates=[\"message\",\"callback_query\"]"

# Verify webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

### Step 9: Test Deployment

**Test Web UI:**
```bash
curl -I https://claude.yourdomain.com
# Should return: HTTP/2 200
```

**Test Telegram Bot:**
1. Open Telegram, find your bot
2. Send `/start`
3. Send text: "Hello"
4. Send voice message: "Check if workspace is empty"
5. Verify bot responds

✅ **Deployment Complete!**

---

## ⚡ Option 2: One-Command Deployment

### Prerequisites

1. **Complete Option 1 once** (to set up project and env vars in Coolify)
2. **Get Coolify API Token:**
   - Coolify UI → Settings → API Tokens → Create Token
   - Copy token (looks like: `coolify_token_...`)

3. **Get Deploy Webhook URL:**
   - Resource → Settings → Webhooks → Copy Deploy Webhook URL
   - Format: `https://coolify.yourdomain.com/api/v1/deploy/...`

### Setup Deployment Script

Create `deploy.sh`:

```bash
#!/bin/bash

# Coolify Deployment Script
# Usage: ./deploy.sh

set -e

# Configuration (edit these values)
COOLIFY_WEBHOOK_URL="https://coolify.yourdomain.com/api/v1/deploy/your-uuid-here"
COOLIFY_API_TOKEN="coolify_token_your-token-here"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting deployment to Coolify...${NC}"

# Trigger deployment
response=$(curl -s -w "\n%{http_code}" --request GET "$COOLIFY_WEBHOOK_URL" \
  --header "Authorization: Bearer $COOLIFY_API_TOKEN")

http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
  echo -e "${GREEN}✅ Deployment triggered successfully!${NC}"
  echo -e "${BLUE}📊 Monitor progress at: https://coolify.yourdomain.com${NC}"
  exit 0
else
  echo -e "${RED}❌ Deployment failed with status code: $http_code${NC}"
  echo "$body"
  exit 1
fi
```

Make executable:
```bash
chmod +x deploy.sh
```

### One-Command Deploy

```bash
# Push changes to git
git add .
git commit -m "Update"
git push origin main

# Trigger deployment
./deploy.sh
```

**Or even simpler, one-liner:**

```bash
# Deploy with curl (set variables first)
export COOLIFY_WEBHOOK_URL="https://coolify.yourdomain.com/api/v1/deploy/..."
export COOLIFY_TOKEN="coolify_token_..."

curl --request GET "$COOLIFY_WEBHOOK_URL" \
  --header "Authorization: Bearer $COOLIFY_TOKEN"
```

---

## 🔄 Option 3: GitHub Actions CI/CD

### Setup Automatic Deployment on Push

**1. Add GitHub Secrets:**

Go to: Repository → Settings → Secrets and variables → Actions → New repository secret

Add:
```
COOLIFY_WEBHOOK_URL = https://coolify.yourdomain.com/api/v1/deploy/...
COOLIFY_API_TOKEN = coolify_token_...
```

**2. Create Workflow File:**

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Coolify

on:
  push:
    branches:
      - main
  workflow_dispatch: # Allow manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Trigger Coolify Deployment
        run: |
          response=$(curl -s -w "\n%{http_code}" --request GET "${{ secrets.COOLIFY_WEBHOOK_URL }}" \
            --header "Authorization: Bearer ${{ secrets.COOLIFY_API_TOKEN }}")

          http_code=$(echo "$response" | tail -n1)

          if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
            echo "✅ Deployment triggered successfully!"
          else
            echo "❌ Deployment failed with status: $http_code"
            exit 1
          fi

      - name: Notify deployment status
        if: always()
        run: |
          echo "Deployment status: ${{ job.status }}"
          echo "View deployment: https://coolify.yourdomain.com"
```

**3. Commit and push:**

```bash
git add .github/workflows/deploy.yml
git commit -m "Add GitHub Actions deployment"
git push origin main
```

**Result:** Now every push to `main` triggers automatic deployment!

---

## 📊 Deployment Verification Checklist

After any deployment method:

### Web UI Check
```bash
# Test HTTPS access
curl -I https://claude.yourdomain.com

# Expected: HTTP/2 200 OK

# Test web terminal loads
curl https://claude.yourdomain.com | grep -i "claudebox"
```

### Telegram Bot Check
- [ ] Send `/start` → Receives welcome message
- [ ] Send `/status` → Shows session info
- [ ] Send `/help` → Shows command list
- [ ] Send text: "Hello" → Claude responds
- [ ] Send voice message → Transcribed and processed

### Service Health Check
```bash
# Check Coolify dashboard
# Both services should show:
- claudebox-web: ✅ Healthy
- telegram-bot: ✅ Healthy
```

### SSL Certificate Check
```bash
# Verify SSL
curl -vI https://claude.yourdomain.com 2>&1 | grep -i "SSL certificate"

# Should show: Let's Encrypt certificate
```

---

## 🔧 Troubleshooting

### Deployment Fails

**Check logs in Coolify:**
```
Resource → Deployments → Latest → View Logs
```

**Common issues:**
- Missing environment variables → Add in Coolify UI
- Docker build errors → Check Dockerfile syntax
- Port conflicts → Verify no other services using ports

### Webhook Returns 401 Unauthorized

**Solution:**
- Verify API token is correct
- Regenerate token in Coolify settings
- Ensure token has deploy permissions

### Services Won't Start

**Check container logs:**
```bash
# SSH to server
ssh root@your-server-ip

# View telegram-bot logs
docker logs <container-name> --tail 100

# Check for errors
```

### SSL Certificate Not Generated

**Verify:**
1. DNS resolves correctly: `dig claude.yourdomain.com`
2. Ports 80, 443 open: `nc -zv your-server-ip 80`
3. Domain is not behind Cloudflare proxy (orange cloud)
4. Wait 10-15 minutes for Let's Encrypt

---

## 📈 Advanced: Deployment Monitoring

### Monitor Deployment Status via API

```bash
# Get deployment status
curl --request GET \
  "https://coolify.yourdomain.com/api/v1/applications/<uuid>/deployments" \
  --header "Authorization: Bearer $COOLIFY_TOKEN"
```

### Slack/Discord Notifications

Configure in Coolify:
```
Settings → Notifications → Add Integration
```

Supports:
- Slack webhooks
- Discord webhooks
- Email notifications
- Telegram notifications

---

## 🎯 Recommended Workflow

**For Development:**
```bash
# Make changes locally
git add .
git commit -m "Feature: xyz"
git push origin main

# Automatic deployment via GitHub Actions
# Or manual: ./deploy.sh
```

**For Production:**
1. Use GitHub Actions for automatic deployment
2. Monitor Coolify dashboard for deployment status
3. Test endpoints after each deployment
4. Keep Coolify and Docker updated

---

## 📝 Summary

**We have:**
- ✅ Detailed manual deployment guide (Option 1)
- ✅ One-command deployment script (Option 2)
- ✅ GitHub Actions CI/CD automation (Option 3)
- ✅ Verification checklist
- ✅ Troubleshooting guide

**Choose:**
- **First time:** Use Option 1 (Manual UI)
- **Quick redeploy:** Use Option 2 (One-command)
- **Ongoing development:** Use Option 3 (GitHub Actions)

All files needed:
- `docker-compose.yml` ✅ (already created)
- `COOLIFY_DEPLOY.md` ✅ (already created)
- `deploy.sh` - Create from template above
- `.github/workflows/deploy.yml` - Create from template above

---

**Last Updated:** February 7, 2026
**Status:** Ready for deployment
**Deployment Time:** 15-20 min (first time), 2-3 min (automated)
