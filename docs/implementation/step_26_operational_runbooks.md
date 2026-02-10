# Step 26: Operational Runbooks

**Estimated Time:** 30 minutes
**Phase:** 7 - Documentation & Handoff
**Prerequisites:** User documentation complete (Step 25)

---

## Overview

This step creates comprehensive operational runbooks for system administrators and operators. These runbooks document routine operations, incident response procedures, maintenance tasks, and emergency procedures. They ensure the system can be maintained effectively with minimal downtime.

### Context

Operational runbooks are essential for:
- Responding quickly to incidents
- Performing routine maintenance without errors
- Onboarding new administrators
- Ensuring consistent operations
- Reducing mean time to recovery (MTTR)

### Goals

- Document all common operations
- Create incident response playbooks
- Define maintenance procedures
- Document rollback procedures
- Establish monitoring and alerting protocols
- Enable independent system management

---

## Implementation Details

### 1. Runbook Structure

Create the following operational documentation:

```
docs/operations/
├── README.md                           # Operations overview
├── daily-operations.md                 # Daily tasks
├── weekly-maintenance.md               # Weekly tasks
├── incident-response.md                # Emergency procedures
├── deployment-runbook.md               # Deployment procedures
├── backup-restore-runbook.md          # Backup/restore procedures
├── monitoring-alerts.md                # Monitoring setup
├── troubleshooting-playbooks.md       # Issue-specific playbooks
└── emergency-contacts.md               # Contact information
```

### 2. Operations Overview

**docs/operations/README.md:**

```markdown
# Operations Guide - Claude Remote Runner

This guide contains operational procedures for system administrators managing the claude-remote-runner production system.

## Quick Links

- [Daily Operations](daily-operations.md) - Routine daily tasks
- [Weekly Maintenance](weekly-maintenance.md) - Scheduled maintenance
- [Incident Response](incident-response.md) - Emergency procedures
- [Deployment](deployment-runbook.md) - Deploy new versions
- [Backup & Restore](backup-restore-runbook.md) - Data recovery
- [Monitoring](monitoring-alerts.md) - Alerts and dashboards
- [Troubleshooting](troubleshooting-playbooks.md) - Common issues

## System Overview

**Production Environment:**
- **Platform:** Coolify on Hetzner VPS
- **Server:** CPX21 (3 vCPU, 8GB RAM)
- **Services:** claudebox-web, telegram-bot, backup
- **Domain:** https://claude.yourdomain.com
- **Monitoring:** Coolify built-in + custom scripts

**Critical Components:**
1. Telegram Bot (telegram-bot container)
2. Web Interface (claudebox-web container)
3. Persistent Volumes (workspace, claude-config)
4. Backup Service (claude-backup container)

## Access Requirements

**Required Access:**
- SSH access to Hetzner VPS
- Coolify admin credentials
- Telegram Bot admin account
- API console access (Anthropic, OpenAI)
- Domain DNS management
- GitHub/GitLab repository access

**Credentials Locations:**
- SSH keys: Stored in password manager
- Coolify login: `https://your-server-ip:8000`
- API keys: Coolify environment variables
- Emergency contacts: See [emergency-contacts.md](emergency-contacts.md)

## On-Call Rotation

**Primary:** [Name] - [Contact]
**Secondary:** [Name] - [Contact]
**Escalation:** [Name] - [Contact]

**Response Times:**
- **P0 (Critical):** 15 minutes
- **P1 (High):** 1 hour
- **P2 (Medium):** 4 hours
- **P3 (Low):** 1 business day

## Standard Operating Procedures

### Before Making Changes

1. ✅ Check current system status
2. ✅ Review change request/ticket
3. ✅ Notify relevant stakeholders
4. ✅ Create backup if needed
5. ✅ Have rollback plan ready

### After Making Changes

1. ✅ Verify change applied successfully
2. ✅ Check monitoring/logs
3. ✅ Test key functionality
4. ✅ Document change
5. ✅ Close ticket/notify stakeholders

## Key Metrics

**Target SLAs:**
- **Uptime:** 99.5% (3.6 hours downtime/month)
- **Response Time:** <5 seconds (90th percentile)
- **Incident Response:** <15 minutes for P0

**Current Status:**
- Check: [Coolify Monitoring Dashboard]
- Logs: `docker logs telegram-bot -f`
- Metrics: `docker stats`

---

**Emergency Hotline:** See [emergency-contacts.md](emergency-contacts.md)
```

### 3. Daily Operations

**docs/operations/daily-operations.md:**

```markdown
# Daily Operations Checklist

Routine tasks to perform daily (or as scheduled).

## Morning Health Check (5 minutes)

### 1. Check System Status

```bash
# SSH to server
ssh your-server

# Check all containers running
docker ps

# Expected output: 3 containers (claudebox-web, telegram-bot, claude-backup)
```

**✅ Success Criteria:**
- All 3 containers show "Up" status
- No containers in "Restarting" loop

### 2. Check Disk Space

```bash
# Check overall disk usage
df -h

# Expected: <70% usage on root filesystem
# Alert if >80%
```

### 3. Review Logs

```bash
# Check for errors in last 24 hours
docker logs telegram-bot --since 24h | grep -i error

# Check for unauthorized access attempts
docker logs telegram-bot --since 24h | grep -i "unauthorized"

# Check for rate limit violations
docker logs telegram-bot --since 24h | grep -i "rate limit"
```

### 4. Verify Backup Created

```bash
# Check latest backup file
ls -lth backups/ | head -5

# Expected: Backup file from last night (2 AM UTC)
# Alert if no backup in last 25 hours
```

### 5. Check API Usage

**Anthropic Console:**
1. Visit: https://console.anthropic.com/
2. Check usage for last 24 hours
3. Verify within budget
4. Alert if >80% of monthly budget used

**OpenAI Dashboard:**
1. Visit: https://platform.openai.com/usage
2. Check Deepgram API usage
3. Verify within expected range
4. Alert if unusual spike

### 6. Test Bot Responsiveness

```bash
# Send test message via Telegram
# Message: "/status"
# Expected: Response within 5 seconds
```

## Afternoon Check (2 minutes)

### Quick Status Check

```bash
# Container health
docker ps

# Recent errors (last 6 hours)
docker logs telegram-bot --since 6h | grep -i error | tail -10

# Resource usage
docker stats --no-stream
```

## End of Day Report (3 minutes)

### Generate Daily Summary

```bash
# Run daily report script
./scripts/daily-report.sh

# Review output:
# - Total requests processed
# - Error rate
# - Average response time
# - Resource usage peaks
# - Security events
```

### Document Issues

If any issues found:
1. Create incident ticket
2. Document in ops log
3. Assign to appropriate team member

---

## Weekly Summary

At end of week, compile:
- Total uptime percentage
- Number of requests processed
- Average response time
- Security events
- API costs (actual vs budget)
- Issues encountered and resolved

Send summary to stakeholders.
```

### 4. Incident Response Playbook

**docs/operations/incident-response.md:**

```markdown
# Incident Response Playbook

Procedures for handling production incidents.

## Incident Classification

### P0 - Critical (System Down)
- **Description:** System completely unavailable
- **Examples:** All services down, data loss, security breach
- **Response Time:** 15 minutes
- **Escalation:** Immediately notify all on-call

### P1 - High (Major Degradation)
- **Description:** Significant functionality impaired
- **Examples:** Bot not responding, web UI down, backup failed
- **Response Time:** 1 hour
- **Escalation:** Notify primary on-call

### P2 - Medium (Minor Degradation)
- **Description:** Some functionality impaired, workarounds exist
- **Examples:** Slow response times, intermittent errors
- **Response Time:** 4 hours
- **Escalation:** Primary on-call handles

### P3 - Low (Minimal Impact)
- **Description:** Minor issues, no immediate impact
- **Examples:** Cosmetic issues, non-critical warnings
- **Response Time:** 1 business day
- **Escalation:** Handle during business hours

---

## Incident Response Process

### 1. Detect and Alert (0-5 minutes)

**Detection Methods:**
- Monitoring alerts
- User reports
- Automated health checks

**Initial Actions:**
1. Acknowledge the alert
2. Classify severity (P0-P3)
3. Start incident timer
4. Open incident channel/ticket

### 2. Assess and Communicate (5-15 minutes)

**Assessment:**
```bash
# Quick system check
ssh your-server
docker ps
docker logs telegram-bot --tail 100
docker stats --no-stream
df -h
```

**Communication:**
1. Post to incident channel: "Incident detected: [brief description]"
2. Set status page (if applicable)
3. Notify affected users (for P0/P1)

### 3. Mitigate and Resolve (15+ minutes)

Follow specific playbook based on incident type:
- [Bot Not Responding](#bot-not-responding)
- [Web UI Down](#web-ui-down)
- [High Error Rate](#high-error-rate)
- [Disk Space Full](#disk-space-full)
- [Security Incident](#security-incident)

### 4. Verify and Monitor (Post-Resolution)

```bash
# Verify services healthy
docker ps
docker logs telegram-bot --tail 50

# Test functionality
# Send test command to bot

# Monitor for 30 minutes
watch -n 60 'docker stats --no-stream'
```

### 5. Document and Follow-Up

1. Update incident ticket with:
   - Root cause
   - Timeline of events
   - Actions taken
   - Resolution

2. Conduct post-mortem (for P0/P1):
   - What happened?
   - Why did it happen?
   - How to prevent in future?

3. Create follow-up tasks
4. Update runbooks if needed

---

## Specific Incident Playbooks

### Bot Not Responding

**Symptoms:**
- Users report bot doesn't respond
- `/start` command doesn't work
- No errors in logs

**Diagnostic Steps:**
```bash
# 1. Check container running
docker ps | grep telegram-bot

# 2. Check logs for errors
docker logs telegram-bot --tail 100

# 3. Check webhook status
curl "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"

# 4. Check network connectivity
docker exec telegram-bot ping -c 3 api.telegram.org
```

**Resolution Steps:**

**Option 1: Restart Container**
```bash
docker compose restart telegram-bot
# Wait 30 seconds
docker logs telegram-bot -f
# Verify "Bot started" message
```

**Option 2: Reset Webhook**
```bash
# Get token from Coolify env vars
curl -X POST "https://api.telegram.org/bot${TOKEN}/setWebhook" \
  -d "url=https://claude.yourdomain.com/${TOKEN}"

# Verify
curl "https://api.telegram.org/bot${TOKEN}/getWebhookInfo"
```

**Option 3: Full Redeploy**
```bash
# Via Coolify UI
# 1. Navigate to application
# 2. Click "Redeploy"
# 3. Monitor logs
```

### Web UI Down

**Symptoms:**
- Cannot access https://claude.yourdomain.com
- 502 Bad Gateway error
- Connection timeout

**Diagnostic Steps:**
```bash
# 1. Check container
docker ps | grep claudebox-web

# 2. Check logs
docker logs claudebox-web --tail 100

# 3. Check port binding
netstat -tlnp | grep 3000

# 4. Check Traefik routing
docker logs coolify-proxy | grep claude
```

**Resolution Steps:**

**Option 1: Restart Web Container**
```bash
docker compose restart claudebox-web
# Wait 30 seconds
docker logs claudebox-web -f
```

**Option 2: Check SSL Certificate**
```bash
# View cert details
echo | openssl s_client -servername claude.yourdomain.com \
  -connect claude.yourdomain.com:443 2>/dev/null | \
  openssl x509 -noout -dates

# If expired, trigger renewal in Coolify UI
```

**Option 3: Verify DNS**
```bash
dig claude.yourdomain.com +short
# Should return your server IP
```

### High Error Rate

**Symptoms:**
- Many errors in logs
- Users report frequent failures
- Monitoring shows >5% error rate

**Diagnostic Steps:**
```bash
# Count recent errors
docker logs telegram-bot --since 1h | grep -c ERROR

# Show unique error types
docker logs telegram-bot --since 1h | grep ERROR | \
  cut -d: -f4- | sort | uniq -c | sort -rn | head -10

# Check resource usage
docker stats --no-stream
```

**Common Causes:**

**1. API Rate Limits Hit**
```bash
# Look for "rate limit" in logs
docker logs telegram-bot --since 1h | grep -i "rate limit"

# Solution: Wait for rate limit reset, or increase limits
```

**2. API Key Invalid**
```bash
# Test API keys
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/messages

# If 401: Regenerate API key in Coolify env vars
```

**3. Out of Memory**
```bash
docker logs telegram-bot | grep -i "killed"
docker logs telegram-bot | grep -i "memory"

# Solution: Increase memory limit in docker-compose.yml
```

### Disk Space Full

**Symptoms:**
- "No space left on device" errors
- Containers failing to write
- Backups failing

**Diagnostic Steps:**
```bash
# Check disk usage
df -h

# Find large directories
du -sh /* 2>/dev/null | sort -rh | head -10

# Check Docker disk usage
docker system df
```

**Resolution Steps:**

**Quick Fix:**
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove old backups
find backups/ -name "*.tar.gz" -mtime +7 -delete

# Clean logs
truncate -s 0 /var/log/syslog
```

**Long-term Fix:**
1. Upgrade VPS to larger disk
2. Implement aggressive log rotation
3. Reduce backup retention period
4. Monitor disk usage daily

### Security Incident

**Symptoms:**
- Unauthorized access detected
- Unusual API usage
- Strange commands in logs
- Security scan findings

**Immediate Actions:**

**1. Contain the Incident**
```bash
# Block suspicious user
# Add to blocked list in code or environment

# Rotate all API keys immediately
# 1. Generate new keys in provider consoles
# 2. Update in Coolify
# 3. Redeploy

# Change web UI password
# Update BASIC_AUTH_PASS in Coolify
```

**2. Assess Impact**
```bash
# Review all logs
docker logs telegram-bot --since 24h > security-incident-$(date +%Y%m%d).log

# Check for data access
grep "file access" security-incident-*.log

# Check for unauthorized commands
grep "unauthorized" security-incident-*.log
```

**3. Investigate**
- Identify attack vector
- Determine what was accessed
- Check if data was exfiltrated
- Review audit logs

**4. Notify**
- Security team (if applicable)
- Affected users (if personal data involved)
- Stakeholders

**5. Remediate**
- Close security holes
- Update security controls
- Document incident
- Plan preventive measures

---

## Post-Incident Review Template

```markdown
# Incident Post-Mortem

**Incident ID:** INC-YYYYMMDD-NNN
**Severity:** P0/P1/P2/P3
**Date:** YYYY-MM-DD
**Duration:** X hours Y minutes
**Responders:** [Names]

## Summary

[Brief description of what happened]

## Impact

- **Users affected:** X
- **Downtime:** X minutes
- **Data loss:** Yes/No
- **Financial impact:** $X

## Timeline

- **HH:MM** - Incident detected
- **HH:MM** - Initial assessment
- **HH:MM** - Mitigation started
- **HH:MM** - Service restored
- **HH:MM** - Incident closed

## Root Cause

[Detailed explanation of why the incident occurred]

## Resolution

[What was done to fix the issue]

## Lessons Learned

### What Went Well
- [Item 1]
- [Item 2]

### What Didn't Go Well
- [Item 1]
- [Item 2]

### Where We Got Lucky
- [Item 1]
- [Item 2]

## Action Items

- [ ] [Action 1] - Owner: [Name] - Due: [Date]
- [ ] [Action 2] - Owner: [Name] - Due: [Date]
- [ ] [Action 3] - Owner: [Name] - Due: [Date]

## Prevention

[How to prevent this incident in the future]
```

---

## Escalation Procedures

### When to Escalate

- P0 incidents lasting >30 minutes
- P1 incidents lasting >2 hours
- Data loss or security breach
- Unable to diagnose issue
- Need additional expertise

### Escalation Path

1. **Level 1:** Primary on-call engineer
2. **Level 2:** Secondary on-call engineer
3. **Level 3:** Engineering lead
4. **Level 4:** CTO/Technical director

### How to Escalate

1. Post in incident channel: "@escalation needed"
2. Call/text next level contact
3. Brief them on situation (2-3 sentences)
4. Transfer incident ownership if needed

---

## Emergency Rollback

If a deployment causes issues:

```bash
# Quick rollback in Coolify UI
# 1. Navigate to application
# 2. Click "Deployments" tab
# 3. Find previous successful deployment
# 4. Click "Redeploy"

# OR via SSH
cd /path/to/claude-remote-runner
git log --oneline
git checkout <previous-working-commit>
docker compose down
docker compose up -d
```

---

**Remember:** During incidents, prioritize:
1. Restore service (mitigation)
2. Communicate clearly
3. Document everything
4. Find root cause (after service restored)
```

### 5. Deployment Runbook

**docs/operations/deployment-runbook.md:**

```markdown
# Deployment Runbook

Standard operating procedure for deploying updates to claude-remote-runner.

## Pre-Deployment Checklist

- [ ] Code reviewed and approved
- [ ] Tests passing on CI/CD
- [ ] Changes documented in changelog
- [ ] Deployment scheduled (avoid peak hours)
- [ ] Stakeholders notified
- [ ] Rollback plan confirmed
- [ ] Backup created

## Deployment Process

### 1. Prepare Deployment (5 minutes)

```bash
# Create pre-deployment backup
ssh your-server
cd /path/to/claude-remote-runner
./scripts/backup-now.sh

# Verify backup created
ls -lh backups/ | head -3
```

### 2. Deploy Update (10 minutes)

**Via Coolify UI (Recommended):**

1. Log into Coolify: https://your-server-ip:8000
2. Navigate to claude-remote-runner application
3. Click "Redeploy" button
4. Monitor deployment logs in real-time
5. Wait for "Deployment successful" message

**Via Git Push (if auto-deploy configured):**

```bash
# On local machine
git push origin main

# Coolify auto-detects and deploys
# Monitor in Coolify UI
```

**Via SSH (manual):**

```bash
ssh your-server
cd /path/to/claude-remote-runner

# Pull latest code
git pull origin main

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Monitor startup
docker compose logs -f
```

### 3. Verify Deployment (5 minutes)

```bash
# Check all containers running
docker ps

# Check logs for startup errors
docker logs telegram-bot --tail 50
docker logs claudebox-web --tail 50

# Verify web UI accessible
curl -I https://claude.yourdomain.com
# Expected: HTTP 200 OK

# Test bot
# Send /start command in Telegram
# Expected: Welcome message

# Send test command
# Expected: Claude responds normally
```

### 4. Monitor Post-Deployment (30 minutes)

```bash
# Watch logs for errors
docker logs telegram-bot -f

# Monitor resource usage
watch -n 10 'docker stats --no-stream'

# Check error rate
docker logs telegram-bot --since 30m | grep -c ERROR
# Should be minimal
```

### 5. Document Deployment

Update deployment log:

```markdown
## Deployment - YYYY-MM-DD HH:MM

**Version:** vX.Y.Z
**Commit:** abc1234
**Deployed by:** [Name]
**Duration:** X minutes

### Changes
- Feature 1
- Bugfix 2
- Update 3

### Issues Encountered
- None / [Description]

### Rollback Needed
- No / Yes - [Reason]
```

## Rollback Procedure

If deployment causes issues:

### Quick Rollback (2 minutes)

```bash
# Via Coolify UI
# 1. Go to "Deployments" tab
# 2. Find previous working deployment
# 3. Click "Redeploy"
# 4. Verify service restored

# Via SSH
cd /path/to/claude-remote-runner
git checkout <previous-commit>
docker compose down
docker compose up -d
```

### Full Rollback with Restore (10 minutes)

```bash
# 1. Stop services
docker compose down

# 2. Restore from backup
./restore-backup.sh backups/claude-backup-YYYYMMDD.tar.gz

# 3. Revert code
git checkout <previous-commit>

# 4. Restart
docker compose up -d

# 5. Verify
docker ps
# Test bot functionality
```

## Deployment Schedule

**Recommended Times:**
- **Best:** Tuesday-Thursday, 10 AM - 2 PM UTC
- **Avoid:** Fridays, weekends, late nights
- **Never:** During known high-traffic periods

**Frequency:**
- **Hotfixes:** As needed (follow expedited process)
- **Minor updates:** Weekly or bi-weekly
- **Major updates:** Monthly with extended testing

## Hotfix Deployment

For critical bug fixes:

1. Create hotfix branch
2. Make minimal changes
3. Fast-track testing
4. Deploy immediately (even off-hours if needed)
5. Monitor closely
6. Document thoroughly

```bash
# Expedited deployment
git checkout -b hotfix/critical-bug
# Make fix
git commit -m "Hotfix: Fix critical bug"
git push origin hotfix/critical-bug

# Deploy via Coolify
# Monitor extra closely
```

---

## Deployment Troubleshooting

### Issue: Deployment fails in Coolify

**Check:**
```bash
# View Coolify logs
docker logs coolify-app

# Check application logs
docker logs telegram-bot
```

**Common Causes:**
- Build errors → Fix code issues
- Environment variables missing → Check Coolify env vars
- Port conflicts → Check port mappings
- Resource limits → Check server resources

### Issue: Containers won't start after deployment

**Check:**
```bash
docker compose config
# Validates docker-compose.yml syntax

docker compose logs
# Shows startup errors
```

**Solutions:**
- Fix docker-compose.yml syntax
- Verify environment variables
- Check volume mounts
- Rollback if needed

---

**Deployment Approval:** All production deployments must be approved by [Role/Person]
```

---

## Acceptance Criteria

- [ ] Operations README created with overview
- [ ] Daily operations checklist documented
- [ ] Incident response playbook complete
- [ ] All incident severity levels defined
- [ ] Specific incident playbooks for common issues
- [ ] Deployment runbook with step-by-step procedures
- [ ] Rollback procedures documented
- [ ] Emergency contacts documented
- [ ] Post-incident review template created
- [ ] Escalation procedures defined

---

## Testing

### Runbook Testing

1. **Practice Incident Response:**
   - Simulate a P1 incident
   - Follow incident response playbook
   - Time how long resolution takes
   - Identify gaps in documentation

2. **Practice Deployment:**
   - Perform a test deployment following runbook
   - Note any missing steps
   - Verify rollback works

3. **Practice Backup/Restore:**
   - Follow backup restore runbook
   - Ensure instructions are complete
   - Time the process

---

## Related Documentation

- [Implementation Plan - Phase 7](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation_plan.md#phase-7-documentation--handoff-1-2-hours)
- [Step 25: User Documentation](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_25_user_documentation.md)
- [Step 27: Cost Analysis](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_27_cost_analysis.md)

---

**Status:** Complete
**Last Updated:** February 4, 2026
**Next Step:** [Step 27: Cost Analysis & Optimization Guide](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_27_cost_analysis.md)
