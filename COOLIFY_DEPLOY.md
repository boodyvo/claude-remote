# Coolify Deployment Guide

This guide walks you through deploying Claude Remote Runner to Coolify.

## Prerequisites

- Coolify installed on your server
- Domain name with DNS configured
- All required API keys ready

## Quick Deployment Steps

### 1. Create New Project in Coolify

1. Log into Coolify dashboard
2. Go to **Projects** → **+ New Project**
3. Set:
   - **Name:** `Claude Remote Runner`
   - **Description:** `Voice-controlled Claude Code with Telegram bot`
4. Click **Create**

### 2. Add Docker Compose Resource

1. In your project, click **+ New Resource**
2. Select **Docker Compose**
3. Choose **Git Repository**
4. Configure:
   - **Repository URL:** `https://github.com/yourusername/claude-remote-runner.git`
   - **Branch:** `main`
   - **Docker Compose Location:** `/docker-compose.yml`
   - **Auto Deploy:** ✓ Enabled
5. Click **Continue**

### 3. Configure Environment Variables

Go to **Environment Variables** tab and add:

#### Required Variables

```env
TELEGRAM_TOKEN=1234567890:ABC...       # Secret ✓
DEEPGRAM_API_KEY=...                   # Secret ✓
WEBHOOK_URL=https://claude.yourdomain.com/${TELEGRAM_TOKEN}
ALLOWED_USER_IDS=123456789             # Your Telegram user ID
```

**Important - Claude Authentication:**
- This project uses **Claude Pro/Max subscription** (NOT API key)
- Before deployment, SSH to your server and run: `claude login`
- Follow the browser authentication flow
- Verify with: `claude` then type `/status` (should show "Claude Pro" or "Claude Max")
- Do NOT set ANTHROPIC_API_KEY environment variable

**Get your Telegram user ID:**
- Message @userinfobot on Telegram
- Copy the user ID it returns

#### Optional Variables

```env
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=your-secure-password   # Secret ✓
BOT_MODE=webhook                        # or 'polling' for local
```

**Generate secure password:**
```bash
openssl rand -base64 32
```

### 4. Configure Domain & SSL

1. Go to **Domains** tab
2. Click **+ Add Domain**
3. Enter: `claude.yourdomain.com`
4. Enable:
   - ✓ HTTPS
   - ✓ Auto SSL (Let's Encrypt)
   - ✓ Force HTTPS
5. Click **Save**

**DNS Configuration:**

Before SSL can be generated, add this DNS record at your domain registrar:

```
Type: A
Name: claude
Value: <your-server-ip>
TTL: 300
```

Verify DNS propagation:
```bash
dig claude.yourdomain.com
```

### 5. Configure Services

The docker-compose.yml automatically configures two services:

**claudebox-web** (Web Terminal):
- Internal Port: 3000
- Domain: claude.yourdomain.com
- Path: /

**telegram-bot** (Telegram Bot):
- Internal Port: 8443 (webhook)
- Domain: claude.yourdomain.com
- Path: /${TELEGRAM_TOKEN}

Coolify's Traefik proxy will handle routing automatically.

### 6. Deploy

1. Click **Deploy** button
2. Monitor logs for:
   - ✓ Building images
   - ✓ Starting containers
   - ✓ Health checks passing
   - ✓ SSL certificate generated
3. Wait for "Deployment successful" message

### 7. Configure Telegram Webhook

After deployment, set the webhook:

```bash
curl -X POST "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook" \
  -d "url=https://claude.yourdomain.com/<YOUR_TOKEN>" \
  -d "allowed_updates=[\"message\",\"callback_query\"]"
```

Verify:
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getWebhookInfo"
```

Should show:
```json
{
  "ok": true,
  "result": {
    "url": "https://claude.yourdomain.com/<YOUR_TOKEN>",
    "has_custom_certificate": false,
    "pending_update_count": 0
  }
}
```

### 8. Test Deployment

**Test Web UI:**
```bash
open https://claude.yourdomain.com
```
Should show the claudebox terminal interface.

**Test Telegram Bot:**
1. Open Telegram
2. Find your bot
3. Send `/start`
4. Send voice message: "Hello, are you working?"
5. Verify bot responds

## Troubleshooting

### Deployment Fails

**Check Coolify logs** for specific errors:
- Environment variables missing → Add them in Coolify UI
- Build errors → Check Dockerfile syntax
- Port conflicts → Verify no other services using ports

### SSL Certificate Not Generated

1. Verify DNS resolves: `dig claude.yourdomain.com`
2. Wait 10-15 minutes for DNS propagation
3. Check ports 80, 443 open on firewall
4. Review Coolify logs for Let's Encrypt errors

### Bot Not Responding

1. Check container logs in Coolify
2. Verify environment variables set correctly
3. Confirm webhook URL matches domain
4. Test webhook endpoint:
   ```bash
   curl https://claude.yourdomain.com/<YOUR_TOKEN>
   ```

### Web UI Shows 502 Error

1. Check claudebox-web container is running
2. Verify health check passing
3. Check Traefik routing logs
4. Restart deployment if needed

## Monitoring

### View Logs

In Coolify:
1. Go to your resource
2. Click **Logs** tab
3. Select service (claudebox-web or telegram-bot)
4. View real-time logs

### Check Health

Services have automatic health checks every 30 seconds. Green checkmark means healthy.

### Resource Usage

Monitor CPU, memory, and network in Coolify dashboard under **Metrics**.

## Updates & Redeployment

### Auto-Deploy from Git

If enabled, pushes to `main` branch trigger automatic deployment.

### Manual Redeploy

1. Go to resource in Coolify
2. Click **Deploy** button
3. Wait for completion

### Rollback

1. Go to **Deployments** tab
2. Find previous successful deployment
3. Click **Redeploy**

## Security Checklist

- [ ] All secrets marked as "Secret" in Coolify
- [ ] HTTPS enabled and forced
- [ ] ALLOWED_USER_IDS configured (restrict bot access)
- [ ] BASIC_AUTH configured for web UI
- [ ] No credentials in git repository
- [ ] Firewall allows only ports 22, 80, 443

## Cost Optimization

- Coolify is free (self-hosted)
- Server: €9/month (Hetzner CPX21)
- APIs: $50-80/month (Anthropic + Deepgram)
- Total: ~$60-90/month

Set spending limits in API provider dashboards.

## Support

- **Coolify Docs:** https://coolify.io/docs
- **Project Issues:** GitHub repository issues
- **Coolify Discord:** Join for community support

---

**Last Updated:** February 7, 2026
**Tested With:** Coolify v4.0.0+
