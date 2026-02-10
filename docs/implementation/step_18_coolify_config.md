# Step 18: Coolify Deployment Configuration

**Estimated Time:** 1 hour
**Phase:** Phase 5 - Production Deployment
**Prerequisites:** Step 17 (Git Repository Preparation) completed successfully
**Status:** Not Started

---

## Overview

This step configures the claude-remote-runner project in Coolify for production deployment. Coolify is a self-hosted PaaS that simplifies deployment, SSL management, and monitoring. This comprehensive guide includes exact UI navigation paths, all configuration values, and Coolify-specific setup requirements.

### Context

Coolify deployment involves:
1. Creating a new project in Coolify UI
2. Connecting your Git repository
3. Configuring environment variables securely
4. Setting up domain and SSL certificates
5. Configuring port mappings and health checks
6. Preparing for initial deployment

This is a critical step that bridges development and production deployment.

### Goals

- ✅ Create Coolify project with proper configuration
- ✅ Configure all environment variables securely
- ✅ Set up domain with automatic SSL
- ✅ Configure Docker Compose service mappings
- ✅ Set up health checks and monitoring
- ✅ Prepare deployment settings
- ✅ Document all configuration for future reference

---

## Implementation Details

### 1. Access Coolify Dashboard

**Navigate to Coolify:**

```bash
# If accessing for first time
https://your-server-ip:8000

# If custom domain configured
https://coolify.yourdomain.com
```

**Login:**
- Use admin credentials created during Coolify installation
- If 2FA enabled, use your authenticator app

### 2. Create New Project

**Navigation Path:**
```
Dashboard → Projects → + New Project
```

**Project Configuration:**

| Field | Value |
|-------|-------|
| **Project Name** | `Claude Remote Runner` |
| **Description** | `Voice-controlled Claude Code with Telegram bot and web UI` |
| **Environment** | `production` (create new if doesn't exist) |

**Click:** `Create Project`

**Expected Result:**
- Project created successfully
- Redirected to project overview page
- Empty resources list displayed

**Screenshot Location:** Coolify UI showing new project creation form

### 3. Add Git Repository Resource

**Navigation Path:**
```
Project Overview → + New Resource → Docker Compose
```

**Source Selection:**

Click: `Git Repository` (not "Docker Compose file on server")

**Repository Configuration:**

| Setting | Value | Notes |
|---------|-------|-------|
| **Git Provider** | `GitHub` / `GitLab` / `Other` | Select your provider |
| **Repository URL** | `https://github.com/yourusername/claude-remote-runner.git` | Full HTTPS URL |
| **Branch** | `main` | Or `master` if using legacy naming |
| **Git Credentials** | `Public Repository` | Or configure SSH key/token if private |
| **Auto Deploy** | `✓ Enabled` | Deploys automatically on git push |

**Docker Compose Configuration:**

| Setting | Value | Notes |
|---------|-------|-------|
| **Docker Compose Location** | `/docker-compose.yml` | Path relative to repository root |
| **Docker Compose Version** | `Auto-detect` | Uses version specified in file |
| **Build Pack** | `Docker Compose` | Auto-selected |

**Click:** `Continue`

**Expected Result:**
- Resource added to project
- Initial repository scan starts
- Configuration tabs appear (Environment, Domains, Deployment, etc.)

### 4. Configure Environment Variables

**Navigation Path:**
```
Resource → Environment Variables tab
```

**Important Notes:**
- Variables marked with `(:?)` in docker-compose.yml are **required**
- Mark sensitive variables as "Secret" (masked in UI and logs)
- Variables are encrypted at rest by Coolify

**Add Each Variable:**

For each variable, click `+ Add` and enter:

#### Required Variables

**1. ANTHROPIC_API_KEY**
```
Key:    ANTHROPIC_API_KEY
Value:  sk-ant-api03-... (your actual key)
Secret: ✓ Yes (check this box)
Build:  ☐ No
```

**2. TELEGRAM_TOKEN**
```
Key:    TELEGRAM_TOKEN
Value:  1234567890:ABC... (your actual token)
Secret: ✓ Yes
Build:  ☐ No
```

**3. DEEPGRAM_API_KEY**
```
Key:    DEEPGRAM_API_KEY
Value:  sk-... (your actual key)
Secret: ✓ Yes
Build:  ☐ No
```

**4. WEBHOOK_URL**
```
Key:    WEBHOOK_URL
Value:  https://claude.yourdomain.com/${TELEGRAM_TOKEN}
Secret: ☐ No (contains variable reference)
Build:  ☐ No
```

**Note:** The `${TELEGRAM_TOKEN}` will be replaced by Coolify at runtime.

**5. ALLOWED_USER_IDS**
```
Key:    ALLOWED_USER_IDS
Value:  123456789,987654321 (your Telegram user IDs)
Secret: ☐ No
Build:  ☐ No
```

**Get your Telegram user ID:**
1. Open Telegram
2. Message @userinfobot
3. Copy your user ID from response

#### Optional Variables

**6. BASIC_AUTH_USER** (recommended for web UI)
```
Key:    BASIC_AUTH_USER
Value:  admin (or your preferred username)
Secret: ☐ No
Build:  ☐ No
```

**7. BASIC_AUTH_PASS** (recommended for web UI)
```
Key:    BASIC_AUTH_PASS
Value:  your-secure-password-here (generate strong password)
Secret: ✓ Yes
Build:  ☐ No
```

**Generate secure password:**
```bash
# On your local machine
openssl rand -base64 32
```

**Click:** `Save` after adding all variables

**Verification Checklist:**
- [ ] All 5 required variables added
- [ ] Sensitive keys marked as Secret
- [ ] WEBHOOK_URL includes correct domain
- [ ] ALLOWED_USER_IDS includes your Telegram ID
- [ ] No typos in variable names
- [ ] No quotes around values (unless value contains spaces)

**Screenshot Location:** Environment Variables tab showing all configured variables (secrets masked)

### 5. Configure Domain and SSL

**Navigation Path:**
```
Resource → Domains tab
```

**Primary Domain Configuration:**

Click: `+ Add Domain`

| Setting | Value | Notes |
|---------|-------|-------|
| **Domain** | `claude.yourdomain.com` | Must be valid FQDN |
| **HTTPS** | `✓ Enabled` | Always enable for production |
| **WWW Redirect** | `☐ Disabled` | Not needed for subdomain |
| **Generate SSL** | `✓ Auto (Let's Encrypt)` | Automatic SSL certificate |

**Advanced SSL Settings (optional):**

Click: `Advanced SSL Settings` (if needed)

| Setting | Value | Notes |
|---------|-------|-------|
| **SSL Provider** | `Let's Encrypt` | Default, recommended |
| **Force HTTPS** | `✓ Enabled` | Redirect HTTP to HTTPS |
| **HSTS** | `✓ Enabled` | Security best practice |
| **HSTS Max Age** | `31536000` | 1 year in seconds |

**Click:** `Save`

**DNS Prerequisites:**

Before SSL can be generated, verify DNS is configured:

```bash
# On your local machine, verify DNS points to server
dig claude.yourdomain.com

# Expected output:
# claude.yourdomain.com. 300 IN A <your-server-ip>
```

**If DNS not configured:**

1. Log into your domain registrar (Namecheap, Cloudflare, etc.)
2. Add A record:
   - **Type:** A
   - **Name:** claude (or your subdomain)
   - **Value:** your-server-ip
   - **TTL:** 300 (5 minutes)
3. Wait 5-10 minutes for propagation
4. Verify with `dig` command above

**Expected Result:**
- Domain added to resource
- SSL certificate generation queued
- Certificate will be generated on first deployment

**Screenshot Location:** Domains tab showing configured domain with SSL enabled

### 6. Configure Service Port Mappings

**Important:** Coolify uses Traefik reverse proxy, so we **do NOT** expose ports directly in docker-compose.yml. Instead, we configure which internal port Traefik should route to.

**Navigation Path:**
```
Resource → Configuration tab → Service Configuration
```

**Service Identification:**

Coolify will detect services from docker-compose.yml:
- `claudebox-web`
- `telegram-bot`

**Configure claudebox-web service:**

Click on `claudebox-web` service card

| Setting | Value | Notes |
|---------|-------|-------|
| **Exposed** | `✓ Yes` | Make accessible via domain |
| **Internal Port** | `3000` | Port service listens on |
| **Public Port** | `(auto)` | Managed by Traefik |
| **Domain** | `claude.yourdomain.com` | Use primary domain |
| **Path Prefix** | `/` | Root path (default) |
| **Strip Prefix** | `☐ No` | Keep path as-is |

**Configure telegram-bot service:**

Click on `telegram-bot` service card

| Setting | Value | Notes |
|---------|-------|-------|
| **Exposed** | `✓ Yes` | Needs to receive webhooks |
| **Internal Port** | `8443` | Port webhook listener uses |
| **Public Port** | `(auto)` | Managed by Traefik |
| **Domain** | `claude.yourdomain.com` | Same domain |
| **Path Prefix** | `/${TELEGRAM_TOKEN}` | Webhook path (secure) |
| **Strip Prefix** | `☐ No` | Keep full path |

**Advanced Settings (both services):**

| Setting | Value | Notes |
|---------|-------|-------|
| **Health Check** | `✓ Enabled` | Use healthcheck from docker-compose.yml |
| **Health Check Interval** | `30s` | From docker-compose.yml |
| **Health Check Retries** | `3` | From docker-compose.yml |
| **Restart Policy** | `unless-stopped` | From docker-compose.yml |

**Click:** `Save` for each service

**Expected Result:**
- Both services configured with proper port mappings
- Traefik will route domain to both services based on path
- Health checks configured for monitoring

**Screenshot Location:** Service Configuration showing both services with port mappings

### 7. Configure Resource Settings

**Navigation Path:**
```
Resource → Settings tab
```

**Build Configuration:**

| Setting | Value | Notes |
|---------|-------|-------|
| **Build Method** | `Docker Compose` | Auto-detected |
| **Docker Compose Command** | `docker compose up -d` | Default |
| **Custom Build Command** | (empty) | Use default |
| **Docker Compose Args** | (empty) | No additional args needed |

**Deployment Configuration:**

| Setting | Value | Notes |
|---------|-------|-------|
| **Deployment Type** | `Rolling` | Zero-downtime deployment |
| **Deployment Webhook** | `✓ Enabled` | For GitHub/GitLab webhooks |
| **Webhook Secret** | `(auto-generated)` | Use for git webhook configuration |
| **Manual Deploy Only** | `☐ No` | Auto-deploy on push |

**Resource Limits (optional but recommended):**

| Setting | Value | Notes |
|---------|-------|-------|
| **Memory Limit (claudebox-web)** | `2048m` | 2GB RAM |
| **Memory Limit (telegram-bot)** | `1024m` | 1GB RAM |
| **CPU Limit** | `(unlimited)` | Or set to 2.0 CPUs if needed |

**Logging Configuration:**

| Setting | Value | Notes |
|---------|-------|-------|
| **Log Driver** | `json-file` | Default Docker logging |
| **Max Log Size** | `10m` | Rotate at 10MB |
| **Max Log Files** | `3` | Keep last 3 rotations |
| **Show in Dashboard** | `✓ Enabled` | View logs in Coolify UI |

**Click:** `Save All Settings`

**Screenshot Location:** Settings tab showing all configurations

### 8. Configure Persistent Volumes

**Navigation Path:**
```
Resource → Volumes tab
```

Coolify automatically detects named volumes from docker-compose.yml:
- `workspace`
- `claude-config`

**Verify Volume Configuration:**

For each volume, verify:

**workspace volume:**
```
Name:        workspace
Mount Path:  /workspace (in containers)
Driver:      local
Backup:      ☐ Configure in Step 22
```

**claude-config volume:**
```
Name:        claude-config
Mount Path:  /root/.claude (in containers)
Driver:      local
Backup:      ☐ Configure in Step 22
```

**Volume Bind Mounts (from docker-compose.yml):**

The following bind mounts are also configured:
- `./bot:/app` (telegram-bot source code)
- `./sessions:/app/sessions` (bot session persistence)

**Important:** Coolify manages these automatically based on docker-compose.yml. No manual configuration needed unless you want to change backup settings.

**Expected Result:**
- All volumes detected and listed
- Mount paths correct
- Volumes will persist across deployments

**Screenshot Location:** Volumes tab showing detected volumes

### 9. Configure Git Webhook (Optional but Recommended)

This enables automatic deployment when you push to your repository.

**For GitHub:**

**Navigation Path:**
```
Resource → Settings tab → Copy Webhook URL
```

**Copy the webhook URL:** (format: `https://coolify.yourdomain.com/api/v1/deploy/...`)

**Then in GitHub:**

1. Go to your repository settings
2. Navigate to: `Settings → Webhooks → Add webhook`
3. Configure:
   ```
   Payload URL:    <paste Coolify webhook URL>
   Content type:   application/json
   Secret:         <paste Coolify webhook secret>
   SSL:            ✓ Enable SSL verification
   Events:         ✓ Just the push event
   Active:         ✓ Yes
   ```
4. Click: `Add webhook`
5. Test: Push a commit and verify deployment triggers

**For GitLab:**

1. Go to: `Settings → Webhooks`
2. Configure similar to GitHub above
3. Use GitLab's webhook format

**Verification:**
```bash
# Make a test commit
git commit --allow-empty -m "Test auto-deploy"
git push origin main

# Watch Coolify logs for deployment start
```

**Screenshot Location:** GitHub webhook configuration page

### 10. Review Complete Configuration

**Final Configuration Checklist:**

Before proceeding to deployment, verify:

**Project Settings:**
- [x] Project name: "Claude Remote Runner"
- [x] Environment: production

**Repository:**
- [x] Git URL correct
- [x] Branch: main
- [x] Auto-deploy enabled
- [x] docker-compose.yml location: /docker-compose.yml

**Environment Variables:**
- [x] ANTHROPIC_API_KEY configured (secret)
- [x] TELEGRAM_TOKEN configured (secret)
- [x] DEEPGRAM_API_KEY configured (secret)
- [x] WEBHOOK_URL configured
- [x] ALLOWED_USER_IDS configured
- [x] BASIC_AUTH_USER configured (optional)
- [x] BASIC_AUTH_PASS configured (secret, optional)

**Domain & SSL:**
- [x] Domain: claude.yourdomain.com
- [x] DNS A record points to server
- [x] HTTPS enabled
- [x] Auto SSL (Let's Encrypt) enabled
- [x] Force HTTPS enabled

**Services:**
- [x] claudebox-web exposed on port 3000
- [x] telegram-bot exposed on port 8443
- [x] Both services have health checks
- [x] Path routing configured

**Volumes:**
- [x] workspace volume detected
- [x] claude-config volume detected
- [x] Bind mounts for bot code

**Settings:**
- [x] Build method: Docker Compose
- [x] Deployment type: Rolling
- [x] Resource limits set
- [x] Logging configured
- [x] Git webhook configured (optional)

**Screenshot Location:** Overview showing green checkmarks for all configured items

---

## Testing Procedures

### Test Case 1: Configuration Validation

**Steps:**
1. Navigate to Resource overview
2. Check for any red warning indicators
3. Review "Pre-deployment Checks" section

**Expected Result:**
- All checks green
- No warnings about missing configuration
- "Ready to Deploy" status shown

**If Issues Found:**
- Review error messages
- Double-check corresponding configuration section
- Fix and re-validate

### Test Case 2: Environment Variable Verification

**Steps:**
1. Go to Environment Variables tab
2. Count variables (should be 7 with optional)
3. Verify secrets are masked (show as `•••••••`)
4. Click "Preview" to see expanded values

**Expected Output:**
```
ANTHROPIC_API_KEY=•••••••••••••••
TELEGRAM_TOKEN=•••••••••••••••
DEEPGRAM_API_KEY=•••••••••••••••
WEBHOOK_URL=https://claude.yourdomain.com/•••••
ALLOWED_USER_IDS=123456789,987654321
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=•••••••••••••••
```

### Test Case 3: DNS Verification

**Steps:**
```bash
# From local machine
dig claude.yourdomain.com

# Should return your server IP
# If not, wait a few minutes and try again
```

**Expected Output:**
```
;; ANSWER SECTION:
claude.yourdomain.com. 300 IN A 95.123.45.67
```

**If Fails:**
- Check DNS configuration at registrar
- Wait for DNS propagation (up to 24 hours, usually 5-10 minutes)
- Try alternate DNS checker: `nslookup claude.yourdomain.com 8.8.8.8`

### Test Case 4: Service Port Configuration

**Steps:**
1. Go to Service Configuration
2. Check claudebox-web shows:
   - Internal: 3000
   - Path: /
3. Check telegram-bot shows:
   - Internal: 8443
   - Path: /${TELEGRAM_TOKEN}

**Verification:**
- Ports match docker-compose.yml
- Paths configured correctly
- Both services marked as "Exposed"

### Test Case 5: Resource Limits Check

**Steps:**
1. Navigate to Settings → Resource Limits
2. Verify memory limits set
3. Calculate total: 2048 + 1024 = 3072 MB

**Expected:**
- Total memory < server RAM (should be <8GB for CPX21)
- Limits prevent any single service from consuming all resources

### Test Case 6: Webhook Test (if configured)

**Steps:**
1. Copy webhook URL from Coolify
2. Test with curl:
   ```bash
   curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"ref":"refs/heads/main"}' \
     https://coolify.yourdomain.com/api/v1/deploy/...
   ```

**Expected Result:**
- Returns 200 OK
- Deployment queued in Coolify
- Logs show webhook received

---

## Screenshots Guidance

### Screenshot 1: Project Creation
**Location:** Coolify UI - New Project form
**Content:**
- Project name field filled
- Environment dropdown selected
- Create button highlighted

### Screenshot 2: Git Repository Configuration
**Location:** Resource configuration page
**Content:**
- Repository URL field
- Branch selection
- Auto-deploy checkbox checked
- Docker Compose location specified

### Screenshot 3: Environment Variables
**Location:** Environment Variables tab
**Content:**
- All 7 variables listed
- Secret variables masked
- Add button visible for future variables

**Annotations:**
- Highlight "Secret" checkboxes
- Point out masked values

### Screenshot 4: Domain Configuration
**Location:** Domains tab
**Content:**
- Primary domain configured
- HTTPS enabled toggle on
- SSL certificate status (pending or active)

### Screenshot 5: Service Configuration
**Location:** Service Configuration section
**Content:**
- Both services (claudebox-web, telegram-bot) shown
- Port mappings visible
- Health check indicators

### Screenshot 6: Deployment Ready Status
**Location:** Resource overview
**Content:**
- All configuration sections with green checkmarks
- "Ready to Deploy" button enabled
- No warning messages

---

## Acceptance Criteria

### Configuration Completeness
- ✅ Project created in Coolify
- ✅ Git repository connected
- ✅ All required environment variables set
- ✅ Optional environment variables configured
- ✅ Domain configured with DNS verified
- ✅ SSL certificate preparation complete
- ✅ Service port mappings configured
- ✅ Health checks defined
- ✅ Resource limits set appropriately

### Security Requirements
- ✅ Sensitive variables marked as "Secret"
- ✅ HTTPS force-enabled
- ✅ BASIC_AUTH configured for web UI
- ✅ ALLOWED_USER_IDS restricts bot access
- ✅ No credentials in git repository
- ✅ Webhook secret configured (if using webhooks)

### Production Readiness
- ✅ Deployment type set to "Rolling"
- ✅ Auto-deploy configured
- ✅ Logging enabled with rotation
- ✅ Resource limits prevent OOM
- ✅ Volumes properly configured
- ✅ Ready to proceed to Step 19 (deployment)

---

## Troubleshooting Guide

### Issue 1: Repository Not Found

**Symptoms:**
- Coolify shows "Repository not accessible" error

**Diagnosis:**
- Verify repository URL is correct
- Check repository is public (or SSH key configured)
- Test git clone manually:
  ```bash
  git clone https://github.com/yourusername/claude-remote-runner.git /tmp/test
  ```

**Solutions:**
1. For private repositories:
   - Add SSH key to Coolify: Settings → SSH Keys
   - Add public key to GitHub/GitLab
   - Use SSH URL instead of HTTPS

2. For public repositories:
   - Verify URL has no typos
   - Try HTTPS URL format

### Issue 2: Environment Variables Not Saving

**Symptoms:**
- Variables disappear after clicking Save

**Diagnosis:**
- Check browser console for errors
- Verify no special characters in variable names

**Solutions:**
1. Reload page and try again
2. Clear browser cache
3. Try different browser
4. Contact Coolify support if persists

### Issue 3: DNS Not Resolving

**Symptoms:**
- `dig` command returns no A record

**Diagnosis:**
```bash
# Check if DNS propagated
dig claude.yourdomain.com @8.8.8.8

# Check from multiple DNS servers
dig claude.yourdomain.com @1.1.1.1
```

**Solutions:**
1. Wait longer (DNS can take up to 24 hours)
2. Verify A record added correctly at registrar
3. Check domain not behind Cloudflare proxy (orange cloud)
4. Use `nslookup` as alternative test

### Issue 4: SSL Certificate Cannot Be Generated

**Symptoms:**
- Coolify shows "SSL certificate generation failed"

**Diagnosis:**
- Check DNS resolves to correct IP
- Verify ports 80 and 443 open:
  ```bash
  nc -zv your-server-ip 80
  nc -zv your-server-ip 443
  ```

**Solutions:**
1. Ensure DNS fully propagated (wait 10+ minutes)
2. Check firewall allows ports 80, 443:
   ```bash
   sudo ufw status
   # Should show 80/tcp and 443/tcp ALLOW
   ```
3. Verify no other service using port 80/443
4. Check Coolify logs for Let's Encrypt errors

### Issue 5: Service Port Conflicts

**Symptoms:**
- Warning about port already in use

**Diagnosis:**
```bash
# SSH to server, check what's using ports
sudo netstat -tlnp | grep :3000
sudo netstat -tlnp | grep :8443
```

**Solutions:**
1. Stop conflicting service
2. Change internal port in docker-compose.yml
3. Let Coolify manage ports (remove port mappings from docker-compose.yml)

### Issue 6: Resource Limits Too High

**Symptoms:**
- Warning: "Resource limits exceed server capacity"

**Diagnosis:**
```bash
# Check server RAM
free -h

# Check current Docker usage
docker stats
```

**Solutions:**
1. Reduce memory limits:
   - claudebox-web: 1024m (instead of 2048m)
   - telegram-bot: 512m (instead of 1024m)
2. Upgrade server if needed (to CPX31 or higher)
3. Remove resource limits (not recommended for production)

### Issue 7: Webhook Not Triggering

**Symptoms:**
- Push to GitHub doesn't trigger deployment

**Diagnosis:**
1. Check GitHub webhook delivery history:
   - GitHub repo → Settings → Webhooks → Recent Deliveries
2. Look for error responses

**Solutions:**
1. Verify webhook URL correct
2. Check webhook secret matches
3. Ensure Coolify accessible from internet
4. Test webhook manually with curl
5. Re-add webhook in GitHub

---

## Rollback Procedure

### If Configuration Needs to Be Reset

**Option 1: Delete and Recreate Resource**

```
Steps:
1. Resource → Settings → Danger Zone → Delete Resource
2. Confirm deletion
3. Start from Step 3 of this guide
```

**Option 2: Modify Existing Configuration**

```
Steps:
1. Identify problematic configuration
2. Navigate to relevant tab
3. Update settings
4. Save changes
5. Verify in overview
```

**Option 3: Reset Specific Settings**

```
For Environment Variables:
1. Environment Variables tab
2. Delete incorrect variables
3. Re-add with correct values

For Domain:
1. Domains tab
2. Remove incorrect domain
3. Add correct domain
4. Wait for SSL regeneration
```

### If Need to Start Over Completely

```bash
# Delete entire project
Coolify UI → Projects → Claude Remote Runner → Delete Project

# Confirm deletion
# All resources, settings, and deployments will be removed
# Persistent volumes may be preserved depending on settings

# Start from Step 2 of this guide
```

**Important:** Before deleting:
- Export environment variable list (screenshot or copy)
- Document any custom configurations
- Ensure no data in volumes needs backup

---

## Additional Notes

### Coolify Version Compatibility

This guide tested with:
- Coolify v4.0.0+
- Docker Engine 24.0+
- Docker Compose v2.20+

Older versions may have different UI or features.

### Coolify Proxy (Traefik)

Coolify uses Traefik as reverse proxy:
- Automatic SSL via Let's Encrypt
- HTTP/2 and HTTP/3 support
- Automatic HTTP → HTTPS redirect
- WebSocket support (needed for web terminal)
- Health check integration

**No manual Traefik configuration needed** - Coolify handles everything.

### Resource Naming Conventions

Coolify prefixes all Docker resources:
- Containers: `<project>-<service>-<id>`
- Volumes: `<project>_<volume_name>`
- Networks: `<project>_<network_name>`

This prevents conflicts with other deployments.

### Cost Optimization

**Coolify is free and open-source**
- No per-deployment fees
- No runtime costs beyond server
- Self-hosted = full control

**Server Costs:**
- Hetzner CPX21: €9/month
- Can host multiple projects on same server
- Scale up/down as needed

### Future Enhancements

After deployment successful:
- [ ] Add staging environment
- [ ] Configure backup automation
- [ ] Set up monitoring alerts
- [ ] Implement CI/CD pipeline
- [ ] Add health check notifications

---

**Document Status:** Complete
**Implementation Status:** Not Started
**Next Step:** Proceed to Step 19 (Production Deployment) once configuration verified
**Estimated Completion:** 1 hour (including verification and testing)
