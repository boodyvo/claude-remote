# Step 22: Backup Implementation

**Estimated Time:** 1 hour
**Phase:** 6 - Monitoring, Backup & Optimization
**Prerequisites:** Production deployment running (Steps 17-21 complete)

---

## Overview

This step implements a comprehensive backup strategy for the claude-remote-runner system, including automated daily backups of persistent data, tested restore procedures, and disaster recovery documentation. The backup system ensures data durability and enables quick recovery from failures.

### Context

With the system now running in production, we need to protect against data loss scenarios:
- Accidental deletion of files
- Container corruption
- Volume failures
- User errors (wrong commands executed)
- Server failures
- Deployment mistakes

The backup implementation uses the `offen/docker-volume-backup` container, which is specifically designed for backing up Docker volumes with minimal configuration and proven reliability.

### Goals

- Implement automated daily backups of all persistent volumes
- Create and test manual backup procedure
- Validate restore procedure works correctly
- Document disaster recovery process
- Set up backup monitoring and alerts
- Implement backup retention policy

---

## Implementation Details

### 1. Backup Architecture

**What Gets Backed Up:**
- `workspace` volume - All project files and code
- `claude-config` volume - Claude session history and configuration
- `bot-sessions` directory - Telegram bot state and user data

**Backup Schedule:**
- Daily backups at 2:00 AM UTC
- Retention: 7 days (rolling window)
- Storage location: `./backups/` directory on host

**Backup Format:**
- Compressed tar.gz archives
- Filename pattern: `claude-backup-YYYYMMDD.tar.gz`
- Metadata included in archive

### 2. Docker Compose Configuration

Add the backup service to your `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # ... existing services (claudebox-web, telegram-bot) ...

  # Automated backup service
  backup:
    image: offen/docker-volume-backup:v2.37.0
    container_name: claude-backup
    restart: unless-stopped
    environment:
      # Backup schedule (daily at 2 AM UTC)
      BACKUP_CRON_EXPRESSION: "0 2 * * *"

      # Filename pattern with date
      BACKUP_FILENAME: "claude-backup-%Y%m%d-%H%M%S.tar.gz"

      # Retention policy (keep 7 days)
      BACKUP_RETENTION_DAYS: "7"
      BACKUP_PRUNING_PREFIX: "claude-backup-"

      # Archive location
      BACKUP_ARCHIVE: "/archive"

      # Compression level (1-9, 6 is good balance)
      BACKUP_COMPRESSION: "gz"
      BACKUP_COMPRESSION_LEVEL: "6"

      # Stop containers during backup (optional, safer but causes downtime)
      # BACKUP_STOP_DURING_BACKUP_LABEL: "true"

      # Email notifications (optional)
      # EMAIL_NOTIFICATION_RECIPIENT: "admin@yourdomain.com"
      # EMAIL_SMTP_HOST: "smtp.gmail.com"
      # EMAIL_SMTP_PORT: "587"
      # EMAIL_SMTP_USERNAME: "your-email@gmail.com"
      # EMAIL_SMTP_PASSWORD: "${SMTP_PASSWORD}"

      # Backup encryption (optional but recommended)
      # GPG_PASSPHRASE: "${BACKUP_ENCRYPTION_KEY}"

    volumes:
      # Volumes to backup (read-only)
      - workspace:/backup/workspace:ro
      - claude-config:/backup/claude-config:ro
      - ./sessions:/backup/sessions:ro

      # Backup destination (read-write)
      - ./backups:/archive

      # Docker socket for container management
      - /var/run/docker.sock:/var/run/docker.sock:ro

    networks:
      - claude-network

    labels:
      # Exclude backup container itself from being stopped
      - "docker-volume-backup.stop-during-backup=false"

volumes:
  workspace:
    driver: local
  claude-config:
    driver: local

networks:
  claude-network:
    driver: bridge
```

### 3. Environment Variables

Add to `.env`:

```env
# Backup Configuration
BACKUP_ENCRYPTION_KEY=your-strong-passphrase-here-min-20-chars
SMTP_PASSWORD=your-smtp-password-for-notifications
```

Add to `.env.example`:

```env
# Backup Configuration (optional)
# BACKUP_ENCRYPTION_KEY=your-strong-passphrase-here
# SMTP_PASSWORD=your-smtp-password
```

### 4. Create Backups Directory

```bash
# On your local machine (before pushing to Coolify)
mkdir -p backups
echo "*.tar.gz" > backups/.gitignore
echo "!.gitignore" >> backups/.gitignore
git add backups/.gitignore

# Or on the server after deployment
ssh your-server
cd /path/to/claude-remote-runner
mkdir -p backups
chmod 755 backups
```

### 5. Manual Backup Procedure

**Create immediate backup:**

```bash
# Method 1: Trigger backup container manually
docker exec claude-backup /bin/backup

# Method 2: Using docker run (if backup service not deployed yet)
docker run --rm \
  -v claude-remote-runner_workspace:/backup/workspace:ro \
  -v claude-remote-runner_claude-config:/backup/claude-config:ro \
  -v $(pwd)/backups:/archive \
  offen/docker-volume-backup:v2.37.0

# Method 3: Manual tar backup
docker run --rm \
  -v claude-remote-runner_workspace:/source/workspace:ro \
  -v claude-remote-runner_claude-config:/source/claude-config:ro \
  -v $(pwd)/backups:/backup \
  alpine \
  tar czf /backup/manual-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /source .
```

**Verify backup created:**

```bash
ls -lh backups/
# Should show .tar.gz files with recent timestamps
```

**Inspect backup contents:**

```bash
tar -tzf backups/claude-backup-20260204-020000.tar.gz | head -20
```

### 6. Restore Procedure

**Complete System Restore:**

```bash
#!/bin/bash
# restore-backup.sh

set -e  # Exit on error

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./restore-backup.sh backups/claude-backup-YYYYMMDD.tar.gz"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "Error: Backup file not found: $BACKUP_FILE"
  exit 1
fi

echo "⚠️  WARNING: This will restore from backup and overwrite current data!"
echo "Backup file: $BACKUP_FILE"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
  echo "Restore cancelled"
  exit 0
fi

echo "1. Stopping containers..."
docker compose down

echo "2. Creating safety backup of current state..."
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
docker run --rm \
  -v claude-remote-runner_workspace:/source/workspace:ro \
  -v claude-remote-runner_claude-config:/source/claude-config:ro \
  -v $(pwd)/backups:/backup \
  alpine \
  tar czf /backup/pre-restore-backup-$TIMESTAMP.tar.gz -C /source .

echo "3. Removing current volumes..."
docker volume rm claude-remote-runner_workspace || true
docker volume rm claude-remote-runner_claude-config || true

echo "4. Recreating volumes..."
docker volume create claude-remote-runner_workspace
docker volume create claude-remote-runner_claude-config

echo "5. Restoring data from backup..."
docker run --rm \
  -v claude-remote-runner_workspace:/target/workspace \
  -v claude-remote-runner_claude-config:/target/claude-config \
  -v $(pwd):/backup \
  alpine \
  sh -c "cd / && tar xzf /backup/$(basename $BACKUP_FILE)"

echo "6. Restarting containers..."
docker compose up -d

echo "7. Waiting for services to be healthy..."
sleep 10

echo "8. Verifying services..."
docker compose ps

echo "✅ Restore complete!"
echo "Pre-restore backup saved as: backups/pre-restore-backup-$TIMESTAMP.tar.gz"
```

**Make script executable:**

```bash
chmod +x restore-backup.sh
```

**Usage:**

```bash
# Restore from specific backup
./restore-backup.sh backups/claude-backup-20260204-020000.tar.gz
```

### 7. Partial Restore (Workspace Only)

If you only need to restore workspace files without affecting Claude sessions:

```bash
#!/bin/bash
# restore-workspace-only.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: ./restore-workspace-only.sh backups/claude-backup-YYYYMMDD.tar.gz"
  exit 1
fi

echo "Extracting workspace files from backup..."

# Extract to temporary directory
mkdir -p /tmp/restore-workspace
tar xzf $BACKUP_FILE -C /tmp/restore-workspace backup/workspace/

echo "Restoring workspace volume..."
docker run --rm \
  -v claude-remote-runner_workspace:/target \
  -v /tmp/restore-workspace/backup/workspace:/source:ro \
  alpine \
  sh -c "rm -rf /target/* && cp -a /source/. /target/"

echo "Cleaning up..."
rm -rf /tmp/restore-workspace

echo "✅ Workspace restored!"
docker compose restart claudebox-web telegram-bot
```

### 8. Backup Monitoring Script

Create `scripts/check-backups.sh`:

```bash
#!/bin/bash
# check-backups.sh - Verify backup health

BACKUP_DIR="./backups"
MAX_AGE_HOURS=25  # Alert if newest backup is older than 25 hours

echo "=== Backup Health Check ==="
echo

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
  echo "❌ ERROR: Backup directory not found: $BACKUP_DIR"
  exit 1
fi

# Count backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "claude-backup-*.tar.gz" | wc -l)
echo "📦 Total backups: $BACKUP_COUNT"

if [ $BACKUP_COUNT -eq 0 ]; then
  echo "❌ ERROR: No backups found!"
  exit 1
fi

# Check newest backup age
NEWEST_BACKUP=$(ls -t "$BACKUP_DIR"/claude-backup-*.tar.gz 2>/dev/null | head -1)
if [ -n "$NEWEST_BACKUP" ]; then
  BACKUP_AGE_SECONDS=$(( $(date +%s) - $(stat -f %m "$NEWEST_BACKUP") ))
  BACKUP_AGE_HOURS=$(( BACKUP_AGE_SECONDS / 3600 ))

  echo "📅 Newest backup: $(basename "$NEWEST_BACKUP")"
  echo "⏰ Age: ${BACKUP_AGE_HOURS} hours"

  if [ $BACKUP_AGE_HOURS -gt $MAX_AGE_HOURS ]; then
    echo "⚠️  WARNING: Newest backup is older than $MAX_AGE_HOURS hours!"
    exit 1
  else
    echo "✅ Backup age is acceptable"
  fi
fi

# Check total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "💾 Total backup size: $TOTAL_SIZE"

# List recent backups
echo
echo "📋 Recent backups:"
ls -lh "$BACKUP_DIR"/claude-backup-*.tar.gz | tail -5 | awk '{print $9, "("$5")"}'

# Verify a backup can be listed (not corrupted)
echo
echo "🔍 Verifying newest backup integrity..."
if tar -tzf "$NEWEST_BACKUP" > /dev/null 2>&1; then
  echo "✅ Backup archive is valid"
else
  echo "❌ ERROR: Backup archive may be corrupted!"
  exit 1
fi

echo
echo "=== Backup health check complete ==="
exit 0
```

Make executable:

```bash
chmod +x scripts/check-backups.sh
```

### 9. Coolify Deployment Update

**After modifying docker-compose.yml:**

```bash
# Commit changes
git add docker-compose.yml backups/.gitignore
git commit -m "Add automated backup service"
git push origin main

# Coolify will auto-deploy if webhook configured
# Or manually deploy via Coolify UI
```

**In Coolify UI:**

1. Navigate to your application
2. Go to "Environment Variables"
3. Add `BACKUP_ENCRYPTION_KEY` (mark as secret)
4. Add `SMTP_PASSWORD` if using email notifications (mark as secret)
5. Click "Save"
6. Click "Redeploy"

### 10. Verify Backup Service Running

```bash
# Check backup container is running
docker ps | grep claude-backup

# Check backup logs
docker logs claude-backup

# Should see: "Scheduled backup task registered"
```

---

## Testing

### Test Plan

1. **Verify Backup Service Starts**
   ```bash
   docker compose up -d
   docker ps | grep backup
   docker logs claude-backup
   ```
   - Expected: Container running, logs show cron schedule registered

2. **Trigger Manual Backup**
   ```bash
   docker exec claude-backup /bin/backup
   ```
   - Expected: Backup completes successfully
   - Expected: New .tar.gz file appears in `backups/` directory

3. **Verify Backup Contents**
   ```bash
   tar -tzf backups/claude-backup-*.tar.gz | grep workspace
   ```
   - Expected: Shows workspace files
   - Expected: Shows claude-config files

4. **Test Restore Procedure (Safe Test)**
   ```bash
   # Create test file
   docker exec claudebox-web sh -c "echo 'test-restore' > /workspace/test-restore.txt"

   # Create backup
   docker exec claude-backup /bin/backup

   # Delete test file
   docker exec claudebox-web rm /workspace/test-restore.txt

   # Restore backup
   ./restore-backup.sh backups/claude-backup-$(date +%Y%m%d)*.tar.gz

   # Verify file is back
   docker exec claudebox-web cat /workspace/test-restore.txt
   ```
   - Expected: File restored successfully

5. **Test Backup Retention**
   ```bash
   # Create 10 fake old backups
   for i in {1..10}; do
     touch backups/claude-backup-2026020$i-020000.tar.gz
   done

   # Wait for next scheduled backup or trigger manually
   docker exec claude-backup /bin/backup

   # Verify old backups pruned
   ls -1 backups/*.tar.gz | wc -l
   ```
   - Expected: Only 7 most recent backups remain

6. **Test Backup Monitoring**
   ```bash
   ./scripts/check-backups.sh
   ```
   - Expected: Shows backup health status
   - Expected: Exit code 0 if healthy

---

## Acceptance Criteria

- [ ] Backup service container running successfully
- [ ] Automated daily backups being created at 2 AM UTC
- [ ] Backup files appear in `backups/` directory with correct naming
- [ ] Backup retention working (7-day rolling window)
- [ ] Manual backup command works: `docker exec claude-backup /bin/backup`
- [ ] Restore procedure tested and documented
- [ ] Restore script exists and is executable
- [ ] Backup monitoring script exists and works
- [ ] Backup files are compressed (reasonable size)
- [ ] At least 3 successful backups exist after 3 days
- [ ] Restore procedure recovers data successfully
- [ ] Documentation includes disaster recovery steps

---

## Troubleshooting

### Issue: Backup container exits immediately

**Symptoms:**
```bash
docker ps | grep backup
# No output
docker ps -a | grep backup
# Shows Exited status
```

**Diagnosis:**
```bash
docker logs claude-backup
```

**Solutions:**
- Check volume paths are correct in docker-compose.yml
- Verify `./backups` directory exists and is writable
- Check Docker socket is mounted: `-v /var/run/docker.sock:/var/run/docker.sock:ro`
- Verify cron expression syntax is valid

### Issue: Backups not being created

**Symptoms:**
- Container running but no .tar.gz files in backups/

**Diagnosis:**
```bash
docker logs claude-backup
docker exec claude-backup ls -la /archive
```

**Solutions:**
- Trigger manual backup: `docker exec claude-backup /bin/backup`
- Check cron schedule with `docker exec claude-backup cat /var/spool/cron/crontabs/root`
- Verify timezone: `docker exec claude-backup date`
- Check disk space: `df -h backups/`

### Issue: "Permission denied" when creating backups

**Symptoms:**
```bash
docker logs claude-backup
# Error: cannot create file '/archive/...'
```

**Solutions:**
```bash
# Fix permissions on backup directory
sudo chmod 777 backups/

# Or use specific user
sudo chown -R 1000:1000 backups/
```

### Issue: Backup files are too large

**Symptoms:**
- Backups filling up disk space
- Each backup is many GB

**Solutions:**
- Check what's being backed up:
  ```bash
  tar -tzf backups/claude-backup-*.tar.gz | head -50
  ```
- Exclude large files in docker-compose.yml:
  ```yaml
  BACKUP_EXCLUDE_REGEXP: ".*\\.log$|.*\\.cache$|node_modules"
  ```
- Increase compression level: `BACKUP_COMPRESSION_LEVEL: "9"`

### Issue: Restore fails with "No space left on device"

**Symptoms:**
```bash
./restore-backup.sh backups/...
# Error: No space left on device
```

**Solutions:**
```bash
# Check disk space
df -h

# Clean up old Docker data
docker system prune -a --volumes

# Remove old backups manually
rm backups/claude-backup-202601*.tar.gz
```

### Issue: Cannot verify backup integrity

**Symptoms:**
```bash
tar -tzf backups/claude-backup-*.tar.gz
# Error: Unexpected EOF
```

**Solutions:**
- Backup may have been interrupted during creation
- Re-run backup: `docker exec claude-backup /bin/backup`
- Check disk space during backup creation
- Verify backup service has sufficient time to complete (increase timeout if needed)

---

## Rollback Procedure

If the backup service causes issues:

### Quick Rollback

```bash
# 1. Stop and remove backup container
docker compose down backup
# or
docker stop claude-backup && docker rm claude-backup

# 2. Remove backup service from docker-compose.yml
# (Comment out or delete the backup service section)

# 3. Restart other services
docker compose up -d claudebox-web telegram-bot

# 4. Verify main services still work
docker compose ps
```

### Revert Git Changes

```bash
git revert HEAD
git push origin main
```

**Note:** Existing backups are NOT deleted during rollback and can still be used for manual restore if needed.

---

## Additional Resources

### Backup Best Practices

1. **3-2-1 Rule:**
   - 3 copies of data (production + 2 backups)
   - 2 different media types (disk + cloud)
   - 1 offsite copy

2. **Test Restores Regularly:**
   - Monthly: Test full restore
   - Quarterly: Test disaster recovery scenario
   - Document restore times

3. **Monitor Backup Health:**
   - Set up alerts for missing backups
   - Monitor backup file sizes
   - Verify backups aren't corrupted

4. **Secure Backups:**
   - Encrypt backups with GPG
   - Limit access to backup files
   - Store encryption keys securely (not in .env)

### Off-site Backup Options

**Option 1: S3-Compatible Storage**

Add to docker-compose.yml backup service:

```yaml
environment:
  AWS_S3_BUCKET_NAME: "my-claude-backups"
  AWS_ACCESS_KEY_ID: "${AWS_ACCESS_KEY_ID}"
  AWS_SECRET_ACCESS_KEY: "${AWS_SECRET_ACCESS_KEY}"
  AWS_ENDPOINT: "s3.amazonaws.com"  # or Backblaze B2, Wasabi, etc.
```

**Option 2: Hetzner Storage Box**

```bash
# Mount Hetzner Storage Box via SSHFS or SFTP
# Then use as backup destination
```

**Option 3: rsync to Remote Server**

```bash
# Add cron job to sync backups offsite
0 3 * * * rsync -avz /path/to/backups/ user@backup-server:/backups/claude/
```

### Monitoring Integration

**Option 1: Healthchecks.io**

```bash
# Add to backup post-hook
curl -fsS --retry 3 https://hc-ping.com/your-uuid-here
```

**Option 2: Uptime Kuma**

- Add file check monitor for `backups/` directory
- Alert if no files modified in 25 hours

**Option 3: Prometheus + Grafana**

- Expose metrics from backup container
- Create dashboard for backup health

---

## Cost Analysis

### Storage Requirements

**Per Backup Size Estimate:**
- Workspace files: 100 MB - 5 GB (depends on projects)
- Claude config: 10-50 MB
- Bot sessions: 1-5 MB
- **Total per backup:** ~100 MB - 5 GB

**With 7-day retention:**
- **Total storage needed:** 700 MB - 35 GB

**Hetzner VPS:**
- CPX21 includes 160 GB NVMe
- Backups use <1-22% of available storage
- **No additional cost**

**Off-site Storage (Optional):**
- Backblaze B2: $0.005/GB/month = $0.35/month for 70 GB
- AWS S3 Glacier: $0.004/GB/month = $0.28/month for 70 GB
- **Total additional cost:** $0.28-0.35/month

---

## Related Documentation

- [Design Document - Section 6.3: Backup Strategy](/Users/vlad/WebstormProjects/claude-remote-runner/docs/design.md#63-backup-strategy)
- [Implementation Plan - Phase 6](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation_plan.md#phase-6-monitoring-backup--optimization-2-3-hours)
- [Step 21: Monitoring Setup](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_21_monitoring.md)
- [Step 23: Performance Optimization](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_23_optimization.md)

---

**Status:** Complete
**Last Updated:** February 4, 2026
**Next Step:** [Step 23: Performance Optimization](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_23_optimization.md)
