# Step 19: Production Deployment

**Estimated Time:** 30 minutes
**Phase:** Phase 5 - Production Deployment
**Prerequisites:** Step 18 (Coolify Configuration) completed and verified
**Status:** Not Started

---

## Overview

This step executes the actual production deployment of claude-remote-runner to Coolify. It involves triggering the deployment, monitoring the build and startup process, verifying all services are healthy, and performing comprehensive post-deployment testing. This is the moment where your configured system goes live.

### Context

The deployment process involves:
1. Triggering deployment from Coolify UI
2. Monitoring Docker image builds
3. Watching container startup sequence
4. Verifying health checks pass
5. Confirming SSL certificate generation
6. Testing all service endpoints
7. Validating logging and monitoring

This is a critical step - if successful, you'll have a fully functional production system.

### Goals

- ✅ Successfully deploy to Coolify production environment
- ✅ Monitor deployment logs in real-time
- ✅ Verify all containers start and become healthy
- ✅ Confirm SSL certificate generated
- ✅ Test web UI accessibility via HTTPS
- ✅ Validate all services responsive
- ✅ Document deployment timestamp and version

---

## Implementation Details

### 1. Pre-Deployment Verification

Before clicking deploy, verify all prerequisites from Step 18:

**Checklist:**

```bash
# From Coolify UI, verify:
□ All environment variables set (7 variables)
□ Domain configured: claude.yourdomain.com
□ DNS resolves: dig claude.yourdomain.com
□ Git repository accessible
□ Docker Compose file location correct
□ Service configurations complete
□ Resource limits appropriate

# From terminal, verify DNS:
dig claude.yourdomain.com +short
# Should return: your-server-ip
```

**Screenshot Location:** Coolify resource overview showing all green checkmarks

### 2. Initiate Deployment

**Navigation Path:**
```
Coolify Dashboard → Projects → Claude Remote Runner → Resource → Deploy
```

**Deployment Options:**

Click the **"Deploy"** button (large blue button in top right)

**Deploy Dialog:**

| Option | Setting | Notes |
|--------|---------|-------|
| **Force Rebuild** | `☐ No` | First deployment doesn't need force |
| **Clear Build Cache** | `☐ No` | Not needed for initial deploy |
| **Restart Only** | `☐ No` | We need full deployment |

Click: **"Deploy Now"**

**Expected Response:**
- Deployment queued message appears
- Redirected to deployment logs page
- Build process starts within 5 seconds

**Screenshot Location:** Deploy button and confirmation dialog

### 3. Monitor Deployment Logs

**Navigation Path:**
```
Automatic redirect to: Resource → Deployments → [Latest Deployment]
```

**Log Phases:**

Watch for these sequential phases in the logs:

#### Phase 1: Repository Clone (30-60 seconds)

```
[INFO] Deployment started: deployment-abc123
[INFO] Cloning repository: https://github.com/yourusername/claude-remote-runner.git
[INFO] Branch: main
[INFO] Commit: abc1234 - "Initial production deployment"
[INFO] Clone successful
```

**Verify:**
- Repository clones without errors
- Correct branch checked out
- Latest commit hash matches your repository

#### Phase 2: Docker Build (2-5 minutes)

```
[INFO] Building services...
[INFO] Building telegram-bot...
[INFO] Step 1/8 : FROM python:3.11-slim
[INFO] Step 2/8 : WORKDIR /app
[INFO] Step 3/8 : COPY bot/requirements.txt .
[INFO] Step 4/8 : RUN apt-get update && apt-get install -y ffmpeg git curl
[INFO] Step 5/8 : RUN pip install --no-cache-dir -r requirements.txt
[INFO] Step 6/8 : COPY bot/ .
[INFO] Step 7/8 : EXPOSE 8443
[INFO] Step 8/8 : CMD ["python", "bot.py"]
[INFO] Successfully built telegram-bot

[INFO] Building claudebox-web...
[INFO] Pulling image: koogle/claudebox:latest
[INFO] Pull complete
```

**Verify:**
- No build errors
- All dependencies install successfully
- Both services build/pull complete

**Common Issues at This Stage:**
- Missing dependencies → Check Dockerfile/docker-compose.yml
- Network timeouts → Retry deployment
- Layer cache issues → Use "Clear Build Cache" option

#### Phase 3: Service Startup (1-2 minutes)

```
[INFO] Creating volumes...
[INFO] Created volume: workspace
[INFO] Created volume: claude-config
[INFO] Starting services...
[INFO] Creating network: claude-network
[INFO] Starting claudebox-web...
[INFO] Starting telegram-bot...
[INFO] Waiting for health checks...
```

**Verify:**
- Volumes created successfully
- Network created
- Both containers start

#### Phase 4: Health Checks (1-2 minutes)

```
[INFO] claudebox-web: Health check 1/3... waiting
[INFO] claudebox-web: Health check 2/3... waiting
[INFO] claudebox-web: Health check 3/3... healthy ✓
[INFO] telegram-bot: Health check 1/3... waiting
[INFO] telegram-bot: Health check 2/3... healthy ✓
[INFO] All services healthy
```

**Verify:**
- Both services pass health checks
- No restart loops
- Health checks complete within timeout (2 minutes)

#### Phase 5: SSL Certificate Generation (30-60 seconds)

```
[INFO] Configuring Traefik routes...
[INFO] Route: claude.yourdomain.com → claudebox-web:3000
[INFO] Route: claude.yourdomain.com/${TELEGRAM_TOKEN} → telegram-bot:8443
[INFO] Requesting SSL certificate from Let's Encrypt...
[INFO] SSL certificate generated successfully ✓
[INFO] Certificate: claude.yourdomain.com
[INFO] Valid until: 2026-05-04 (90 days)
```

**Verify:**
- SSL certificate generated without errors
- Valid for 90 days (Let's Encrypt standard)
- Traefik routes configured

**If SSL Fails:**
- Check DNS resolves correctly
- Verify ports 80, 443 open
- Wait a few minutes and retry
- Check Traefik logs: `docker logs coolify-proxy`

#### Phase 6: Deployment Complete

```
[SUCCESS] Deployment completed successfully
[INFO] Deployment ID: deployment-abc123
[INFO] Duration: 4m 32s
[INFO] Services: 2/2 healthy
[INFO] SSL: Active
[INFO] Status: Running

[INFO] Application URLs:
[INFO] - Web UI: https://claude.yourdomain.com
[INFO] - Webhook: https://claude.yourdomain.com/<token>
```

**Screenshot Location:** Complete deployment log showing success message

### 4. Post-Deployment Verification

#### 4.1 Verify Container Status

**Via Coolify UI:**

```
Resource → Overview → Services
```

Check each service shows:
- **claudebox-web**: 🟢 Running (healthy)
- **telegram-bot**: 🟢 Running (healthy)

**Via SSH (optional):**

```bash
# SSH to server
ssh root@your-server-ip

# Check containers
docker ps | grep claude-remote-runner

# Expected output:
# CONTAINER ID   IMAGE                      STATUS         PORTS     NAMES
# abc123...      koogle/claudebox:latest    Up 2 min (healthy)      claude-remote-runner-claudebox-web-1
# def456...      python:3.11-slim           Up 2 min (healthy)      claude-remote-runner-telegram-bot-1
```

#### 4.2 Verify SSL Certificate

**Browser Test:**

```bash
# Open in browser (should show lock icon)
https://claude.yourdomain.com
```

**Command Line Test:**

```bash
# Check SSL certificate
curl -I https://claude.yourdomain.com

# Expected output includes:
# HTTP/2 200
# strict-transport-security: max-age=31536000

# Detailed SSL info
openssl s_client -connect claude.yourdomain.com:443 -servername claude.yourdomain.com < /dev/null | grep -i "verify return code"

# Expected: Verify return code: 0 (ok)
```

**Screenshot Location:** Browser showing HTTPS lock icon and valid certificate

#### 4.3 Test Web UI Access

**Steps:**

1. Open browser to: `https://claude.yourdomain.com`

2. If Basic Auth configured:
   - Enter username (from BASIC_AUTH_USER)
   - Enter password (from BASIC_AUTH_PASS)
   - Click login

3. Verify terminal interface loads:
   - Black terminal screen appears
   - Cursor blinking
   - Can type commands

4. Test Claude Code:
   ```bash
   # In web terminal, type:
   claude --version

   # Should show:
   # Claude Code version X.X.X

   # Test simple command:
   claude -p "What is 2+2?"

   # Should show Claude's response
   ```

**Expected Result:**
- Web UI loads over HTTPS
- Terminal interactive
- Claude commands work
- No JavaScript errors in console (F12)

**Screenshot Location:** Web terminal showing successful Claude command execution

#### 4.4 Verify Container Logs

**Via Coolify UI:**

```
Resource → Logs → Select Service
```

**claudebox-web logs:**
```
Server running on port 3000
Claude Code initialized
WebSocket server started
```

**telegram-bot logs:**
```
INFO - Starting bot with webhook: https://claude.yourdomain.com/...
INFO - Bot started successfully
INFO - Webhook configured
```

**Via SSH:**

```bash
# Check claudebox-web logs
docker logs claude-remote-runner-claudebox-web-1 --tail 50

# Check telegram-bot logs
docker logs claude-remote-runner-telegram-bot-1 --tail 50

# Follow logs in real-time
docker logs -f claude-remote-runner-telegram-bot-1
```

**Verify:**
- No error messages
- Services initialized correctly
- Webhook URL logged (telegram-bot)

#### 4.5 Test Volume Persistence

**Steps:**

```bash
# SSH to server
ssh root@your-server-ip

# Check workspace volume
docker exec claude-remote-runner-claudebox-web-1 ls -la /workspace

# Check claude-config volume
docker exec claude-remote-runner-telegram-bot-1 ls -la /root/.claude

# Check sessions directory
docker exec claude-remote-runner-telegram-bot-1 ls -la /app/sessions
```

**Expected Output:**
- Workspace directory exists and writable
- .claude directory exists (may be empty initially)
- sessions directory exists

**Create test file:**

```bash
# Via web UI terminal
echo "test" > /workspace/test.txt

# Restart container
docker restart claude-remote-runner-claudebox-web-1

# Verify file persists
docker exec claude-remote-runner-claudebox-web-1 cat /workspace/test.txt
# Should show: test
```

### 5. Service-Specific Testing

#### 5.1 Test Telegram Bot (Webhook)

This will be fully tested in Step 20, but verify basic connectivity:

```bash
# Check webhook endpoint responds
curl -I https://claude.yourdomain.com/${TELEGRAM_TOKEN}

# Expected (before webhook set):
# HTTP/2 404 (endpoint exists but no webhook configured yet)

# Or if using the correct full path:
# HTTP/2 200
```

**Note:** Full Telegram bot testing happens in Step 20 after webhook configuration.

#### 5.2 Test Health Endpoints

```bash
# Test claudebox-web health
curl http://localhost:3000/health
# Expected: 200 OK or health check response

# Test telegram-bot health (if implemented)
curl http://localhost:8443/health
# Expected: 200 OK or similar
```

### 6. Document Deployment

**Create Deployment Record:**

Create a file to track this deployment:

**File:** `DEPLOYMENT.md` (add to repository)

```markdown
# Deployment Record

## Production Deployment

**Date:** 2026-02-04
**Time:** 15:30 UTC
**Deployed By:** Your Name
**Deployment ID:** deployment-abc123
**Git Commit:** abc1234567890
**Git Message:** "Initial production deployment"

### Deployment Details

**Server:**
- Provider: Hetzner
- Type: CPX21
- IP: 95.123.45.67
- Location: Nuremberg (nbg1)

**Domain:**
- URL: https://claude.yourdomain.com
- SSL: Let's Encrypt
- Certificate Valid Until: 2026-05-04

**Services:**
- claudebox-web: ✓ Healthy
- telegram-bot: ✓ Healthy

**Volumes:**
- workspace: Created
- claude-config: Created

**Build Time:** 4m 32s
**Deployment Status:** SUCCESS

### Verification Checklist

- [x] Containers running
- [x] Health checks passing
- [x] SSL certificate valid
- [x] Web UI accessible
- [x] Logs show no errors
- [x] Volumes persisting data
- [x] DNS resolving correctly
- [ ] Telegram webhook configured (Step 20)

### Notes

First production deployment. All services healthy.
No issues encountered during deployment.
```

**Commit this file:**

```bash
git add DEPLOYMENT.md
git commit -m "Add deployment record for production"
git push origin main
```

### 7. Enable Monitoring

**Via Coolify UI:**

```
Resource → Monitoring → Enable Monitoring
```

**Settings:**
- [x] Enable monitoring
- [x] Collect metrics every 30s
- [x] Retention: 7 days
- [x] Alert on service down

**Metrics Available:**
- CPU usage (%)
- Memory usage (MB)
- Network I/O (MB)
- Disk I/O (MB)
- Container restarts

**Screenshot Location:** Monitoring dashboard showing metrics graphs

---

## Testing Procedures

### Test Case 1: End-to-End Deployment Success

**Steps:**
1. Click Deploy button
2. Monitor logs from start to finish
3. Verify all phases complete

**Expected Outcome:**
- Deployment completes in <10 minutes
- Success message displayed
- All services healthy
- No errors in logs

### Test Case 2: Service Restart Resilience

**Steps:**
```bash
# Restart individual service
docker restart claude-remote-runner-telegram-bot-1

# Wait 30 seconds
sleep 30

# Check status
docker ps | grep telegram-bot
```

**Expected Outcome:**
- Container restarts successfully
- Health check passes again
- No data loss
- Logs show clean restart

### Test Case 3: Web UI Functionality

**Steps:**
1. Open `https://claude.yourdomain.com`
2. Login with Basic Auth (if enabled)
3. Type in terminal: `ls /workspace`
4. Type: `claude -p "hello"`

**Expected Outcome:**
- Terminal responsive
- Commands execute
- Claude responds
- No errors

### Test Case 4: SSL Certificate Validation

**Steps:**
```bash
# Check certificate
echo | openssl s_client -showcerts -servername claude.yourdomain.com -connect claude.yourdomain.com:443 2>/dev/null | openssl x509 -inform pem -noout -text

# Check expiry
echo | openssl s_client -servername claude.yourdomain.com -connect claude.yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates
```

**Expected Output:**
```
notBefore=Feb  4 14:30:00 2026 GMT
notAfter=May  4 14:30:00 2026 GMT
```

### Test Case 5: Volume Persistence After Deployment

**Steps:**
1. Create file via web UI: `echo "test" > /workspace/test.txt`
2. Re-deploy application (click Deploy again)
3. After deployment, check: `cat /workspace/test.txt`

**Expected Outcome:**
- File still exists
- Content preserved
- No data loss during re-deployment

### Test Case 6: Log Accessibility

**Steps:**
1. Generate some activity (access web UI)
2. View logs in Coolify: Resource → Logs
3. Check logs via SSH: `docker logs <container>`

**Expected Outcome:**
- Logs visible in Coolify UI
- Real-time updates working
- Historical logs retained
- No permission errors

### Test Case 7: Resource Usage Check

**Steps:**
```bash
# Check memory usage
docker stats --no-stream | grep claude-remote-runner

# Expected output format:
# CONTAINER               CPU %   MEM USAGE / LIMIT
# claudebox-web           2.5%    450MB / 2GB
# telegram-bot            1.2%    180MB / 1GB
```

**Verification:**
- Memory usage within limits
- CPU usage reasonable (<50% sustained)
- No OOM (out of memory) kills

---

## Screenshots Guidance

### Screenshot 1: Deployment Initiation
**Location:** Coolify UI
**Content:**
- Deploy button highlighted
- Deployment dialog with options

### Screenshot 2: Build Progress
**Location:** Deployment logs page
**Content:**
- Live log stream
- Docker build steps
- Progress indicators

### Screenshot 3: Successful Deployment
**Location:** Deployment logs completion
**Content:**
- Success message
- Deployment summary
- Service health status
- Duration and timestamps

### Screenshot 4: Services Overview
**Location:** Resource overview page
**Content:**
- Both services showing green (healthy)
- Running status
- Resource usage metrics

### Screenshot 5: Web UI Access
**Location:** Browser
**Content:**
- https://claude.yourdomain.com loaded
- Valid SSL certificate (lock icon)
- Terminal interface displaying
- Cursor blinking

### Screenshot 6: SSL Certificate
**Location:** Browser certificate viewer
**Content:**
- Certificate details
- Issued by Let's Encrypt
- Valid dates shown

---

## Acceptance Criteria

### Deployment Success Criteria
- ✅ Deployment completes without errors
- ✅ Duration <10 minutes
- ✅ All services transition to "healthy" status
- ✅ SSL certificate generated automatically
- ✅ No container restart loops

### Service Health Criteria
- ✅ claudebox-web: Running and healthy
- ✅ telegram-bot: Running and healthy
- ✅ Both services pass health checks
- ✅ No error logs during startup
- ✅ Resource usage within limits

### Accessibility Criteria
- ✅ Web UI accessible via HTTPS
- ✅ SSL certificate valid and trusted
- ✅ No certificate warnings
- ✅ Basic Auth working (if enabled)
- ✅ Terminal interactive and responsive

### Persistence Criteria
- ✅ Volumes created successfully
- ✅ Data persists across container restarts
- ✅ Sessions directory writable
- ✅ Workspace directory accessible
- ✅ Claude config directory exists

### Monitoring Criteria
- ✅ Logs accessible in Coolify UI
- ✅ Metrics collecting every 30s
- ✅ Resource usage graphs visible
- ✅ No anomalies in metrics

---

## Troubleshooting Guide

### Issue 1: Deployment Fails at Build Stage

**Symptoms:**
- Build errors in logs
- Dependency installation fails

**Diagnosis:**
```bash
# Check specific error in logs
# Look for lines with "ERROR" or "FAILED"
```

**Solutions:**
1. Network timeout → Retry deployment
2. Invalid Dockerfile → Review Dockerfile syntax
3. Missing dependencies → Update requirements.txt
4. Build cache issue → Enable "Clear Build Cache"

### Issue 2: Health Checks Failing

**Symptoms:**
- Container starts but health check never passes
- Coolify shows "unhealthy" status

**Diagnosis:**
```bash
# Check container logs
docker logs claude-remote-runner-telegram-bot-1 --tail 100

# Test health check manually
docker exec claude-remote-runner-telegram-bot-1 curl -f http://localhost:8443/health
```

**Solutions:**
1. Service not listening on expected port
2. Health check URL incorrect
3. Service taking too long to start → Increase start_period in docker-compose.yml
4. Dependencies not installed → Check Dockerfile

### Issue 3: SSL Certificate Generation Failed

**Symptoms:**
- "SSL certificate request failed" in logs
- HTTPS not working

**Diagnosis:**
```bash
# Check DNS
dig claude.yourdomain.com +short

# Check ports
sudo netstat -tlnp | grep -E ':(80|443)'

# Check Traefik logs
docker logs coolify-proxy | grep -i certificate
```

**Solutions:**
1. DNS not propagated → Wait 10-30 minutes
2. Ports blocked → Check firewall (ufw allow 80/tcp, ufw allow 443/tcp)
3. Domain mismatch → Verify domain spelling
4. Let's Encrypt rate limit → Wait 1 hour, use staging first

### Issue 4: Container Exits Immediately

**Symptoms:**
- Container shows as "Exited" right after start
- Restart loop

**Diagnosis:**
```bash
# Check exit reason
docker inspect claude-remote-runner-telegram-bot-1 | grep -A 10 "State"

# Check last logs
docker logs claude-remote-runner-telegram-bot-1
```

**Solutions:**
1. Missing environment variable → Check .env
2. Port already in use → Change port
3. Command syntax error → Review docker-compose.yml
4. File not found → Check paths in Dockerfile

### Issue 5: Web UI Not Accessible

**Symptoms:**
- Browser shows "Connection refused" or "502 Bad Gateway"

**Diagnosis:**
```bash
# Check if container running
docker ps | grep claudebox-web

# Check Traefik routing
docker logs coolify-proxy | grep claude.yourdomain.com

# Test locally
curl -I http://localhost:3000
```

**Solutions:**
1. Container not running → Check logs, restart
2. Traefik routing issue → Verify domain in Coolify
3. Firewall blocking → Check server firewall rules
4. Service not listening → Check application startup logs

### Issue 6: Volume Mount Issues

**Symptoms:**
- Permission denied errors
- Files not persisting

**Diagnosis:**
```bash
# Check volume exists
docker volume ls | grep workspace

# Check mount points
docker inspect claude-remote-runner-claudebox-web-1 | grep -A 10 Mounts

# Check permissions
docker exec claude-remote-runner-claudebox-web-1 ls -la /workspace
```

**Solutions:**
1. Volume not created → Recreate with docker-compose
2. Permission issues → Fix with chmod/chown
3. Volume driver issue → Use local driver
4. Bind mount path incorrect → Verify paths in docker-compose.yml

---

## Rollback Procedure

### Immediate Rollback (Failed Deployment)

If deployment fails and services are down:

**Step 1: Stop Failed Deployment**

```
Coolify UI → Resource → Stop All Services
```

**Step 2: Review Logs**

Identify specific failure point from deployment logs.

**Step 3: Fix Issue**

- Update configuration (env vars, docker-compose.yml, etc.)
- Commit changes if needed
- Push to repository

**Step 4: Retry Deployment**

```
Coolify UI → Resource → Deploy (with "Force Rebuild" if needed)
```

### Rollback to Previous Version

If deployment succeeded but application has issues:

**Via Coolify UI:**

```
Resource → Deployments → [Previous Successful Deployment] → Redeploy
```

**Via Git:**

```bash
# Find last working commit
git log --oneline

# Revert to that commit
git checkout <commit-hash>
git push --force origin main

# Coolify will auto-deploy (if webhook configured)
# Or manually deploy from Coolify UI
```

### Emergency Rollback (All Services Down)

**Step 1: SSH to Server**

```bash
ssh root@your-server-ip
```

**Step 2: Stop All Containers**

```bash
cd /path/to/coolify/apps/claude-remote-runner
docker-compose down
```

**Step 3: Restore Previous State**

```bash
# If you have backups
docker run --rm -v workspace:/target alpine sh -c "rm -rf /target/* && tar xzf /backup/workspace.tar.gz -C /target"

# Or fresh start
docker volume rm claude-remote-runner_workspace
docker volume rm claude-remote-runner_claude-config
```

**Step 4: Redeploy via Coolify**

Use Coolify UI to trigger new deployment with fixes applied.

---

## Additional Notes

### Deployment Best Practices

**Before Every Deployment:**
1. Review git diff to see what's changing
2. Test changes locally with docker-compose
3. Backup critical volumes
4. Document expected changes
5. Plan rollback strategy

**During Deployment:**
1. Monitor logs continuously
2. Watch for error messages
3. Note any warnings
4. Track deployment duration
5. Verify each phase completes

**After Deployment:**
1. Test all critical functionality
2. Monitor resource usage for 30 minutes
3. Check error logs
4. Verify webhooks work
5. Update deployment documentation

### Performance Baseline

After first successful deployment, record baseline metrics:

```
CPU Usage (claudebox-web): ~2-5% idle
Memory Usage (claudebox-web): ~400-500 MB
CPU Usage (telegram-bot): ~1-3% idle
Memory Usage (telegram-bot): ~150-200 MB

Deployment Time: 4-6 minutes
SSL Generation Time: 30-60 seconds
Container Startup: 1-2 minutes
Health Check Pass: <2 minutes
```

Use these baselines to identify performance issues in future deployments.

### Zero-Downtime Deployments

For future updates, Coolify supports zero-downtime rolling deployments:

1. New containers start
2. Health checks pass
3. Traffic switches to new containers
4. Old containers stop

This ensures no service interruption during updates.

---

**Document Status:** Complete
**Implementation Status:** Not Started
**Next Step:** After successful deployment, proceed to Step 20 (Webhook Configuration)
**Estimated Completion:** 30 minutes (including testing and verification)
