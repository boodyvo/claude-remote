# File Browser Setup Guide

## Overview

File Browser provides web-based access to the workspace filesystem, allowing you to browse, view, and edit files through your browser.

**Access:** `https://files.yourdomain.com` (after Coolify deployment)
**Local:** `http://localhost:8080` (during testing)

---

## Security Configuration

### Authentication
- ✅ Authentication **enabled** (FB_NOAUTH=false)
- ✅ User signup **disabled** (only admin can create users)
- ✅ Password-based authentication
- ✅ Admin account required for access

### Permissions
- **PUID/PGID:** 0:0 (root) - Matches workspace volume permissions
- **Volume access:** Read-only (`:ro` mount) - Cannot modify files
- **User permissions:** Read-only by default (download only)
- **Scope:** Limited to `/workspace` directory only

**Security Note:** Workspace is mounted read-only. Even admins cannot modify files through File Browser.

### Network Security
- Runs on internal network (claude-network)
- Exposed via Coolify's Traefik reverse proxy
- HTTPS enforced (Let's Encrypt SSL)
- No direct port exposure in production

---

## First-Time Setup

### Step 1: Initial Deployment

The service will start automatically when you deploy via Coolify. On first boot, File Browser generates:
- Admin user: `admin`
- Auto-generated password (displayed in logs **once only**)

### Step 2: Get Initial Admin Password

**Option A: Check Docker logs**
```bash
docker-compose logs file-browser | grep -i "password\|admin"
```

**Option B: View logs in Coolify**
1. Go to your resource in Coolify
2. Click "Logs" tab
3. Select "file-browser" service
4. Look for line: `admin password is: <random-password>`

**Option C: Reset if missed**
```bash
# Stop service
docker-compose stop file-browser

# Remove database
rm filebrowser.db

# Start service (generates new password)
docker-compose up -d file-browser

# Check logs immediately
docker-compose logs file-browser
```

### Step 3: First Login

1. Access File Browser:
   - Local: `http://localhost:8080`
   - Production: `https://files.yourdomain.com`

2. Login with:
   - Username: `admin`
   - Password: (from logs)

3. **Immediately change password:**
   - Click Settings (gear icon) → User Management
   - Click on "admin" user
   - Change password to something secure (20+ characters)
   - Save changes

### Step 4: Create Additional Users (Optional)

1. Settings → User Management → **+ New User**
2. Configure:
   ```
   Username: developer
   Password: <secure-password>
   Scope: /srv
   Locale: en

   Permissions:
   ✓ Execute
   ✓ Create
   ✓ Rename
   ✓ Modify
   ✓ Delete
   ✓ Download
   ☐ Admin
   ☐ Share
   ```
3. Click **Save**

---

## Coolify Deployment

### Step 1: Configure Domain

In Coolify UI:

1. Go to your resource → **Domains** tab
2. Click **+ Add Domain**
3. Configure:
   ```
   Domain: files.yourdomain.com
   Service: file-browser
   Port: 80

   ✓ HTTPS
   ✓ Auto SSL (Let's Encrypt)
   ✓ Force HTTPS
   ```
4. Click **Save**

### Step 2: DNS Configuration

Add A record in your domain registrar:

```
Type: A
Name: files
Value: <your-server-ip>
TTL: 300
```

Verify:
```bash
dig files.yourdomain.com
```

### Step 3: Deploy

Coolify will automatically deploy when you push changes. The file-browser service will start alongside telegram-bot.

### Step 4: Verify Deployment

```bash
# Check service status in Coolify dashboard
# Both services should show: ✅ Healthy

# Test access
curl -I https://files.yourdomain.com
# Expected: HTTP/2 200 OK
```

---

## Usage

### Browsing Files

1. Navigate directories by clicking folders
2. Click files to preview (images, text, markdown, PDF)
3. Use search bar to find files
4. Breadcrumb navigation at top

### Editing Files

1. Click on a text file (`.py`, `.md`, `.txt`, `.json`, etc.)
2. Click **Edit** button (pencil icon)
3. Make changes in editor
4. Click **Save**

### Uploading Files

1. Navigate to target directory
2. Click **Upload** button (up arrow icon)
3. Drag & drop or select files
4. Files upload with progress indicator

### Downloading Files

1. Select file(s) with checkboxes
2. Click **Download** button (down arrow icon)
3. Files download as ZIP if multiple selected

### Managing Files

**Create folder:**
- Click **+** button → New Folder
- Enter name → Create

**Rename:**
- Right-click file → Rename
- Or: Select file → More actions → Rename

**Delete:**
- Select file(s) with checkboxes
- Click **Delete** button (trash icon)
- Confirm deletion

**Move:**
- Select file(s)
- Click **Move** button
- Navigate to destination → Move here

---

## Security Best Practices

### 1. Strong Passwords
```bash
# Generate secure password
openssl rand -base64 32
```

Use passwords with:
- Minimum 20 characters
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words

### 2. Limit User Access

Create separate users for different purposes:
- **admin:** Full access, rarely used
- **developer:** Day-to-day file operations
- **viewer:** Read-only access (if needed)

### 3. Regular Password Rotation

Change passwords every 90 days:
1. Settings → User Management
2. Select user → Change password
3. Update in password manager

### 4. Disable Unused Features

In `filebrowser-config.json`:
```json
{
  "signup": false,           // ✓ Already disabled
  "defaults": {
    "perm": {
      "share": false,        // ✓ File sharing disabled
      "admin": false         // ✓ No admin by default
    }
  }
}
```

### 5. Monitor Access Logs

```bash
# View File Browser logs
docker-compose logs -f file-browser

# Check for suspicious activity
docker-compose logs file-browser | grep -i "login\|fail\|error"
```

### 6. HTTPS Only

✅ Already enforced via Coolify (Force HTTPS enabled)

### 7. Network Isolation

✅ File Browser runs on isolated Docker network
✅ Only accessible via Coolify proxy
✅ No direct internet exposure

---

## Troubleshooting

### Issue: Can't access web UI

**Check service status:**
```bash
docker-compose ps file-browser
```

**Check logs:**
```bash
docker-compose logs file-browser
```

**Verify port binding:**
```bash
netstat -tulpn | grep 8080
```

**Restart service:**
```bash
docker-compose restart file-browser
```

### Issue: Permission denied when editing files

**Solution 1: Check workspace permissions**
```bash
# Check ownership
docker exec -it telegram-bot ls -la /workspace

# Should show root:root or accessible UID
```

**Solution 2: Verify PUID/PGID**
```yaml
# In docker-compose.yml
environment:
  - PUID=0    # Must match workspace owner
  - PGID=0
```

### Issue: Forgot admin password

**Reset database:**
```bash
# Stop service
docker-compose stop file-browser

# Backup existing database
cp filebrowser.db filebrowser.db.backup

# Remove database
rm filebrowser.db

# Restart (generates new admin password)
docker-compose up -d file-browser

# Get new password from logs
docker-compose logs file-browser | grep password
```

### Issue: Database locked error

**Cause:** Multiple File Browser instances accessing same database

**Solution:**
```bash
# Ensure only one instance running
docker ps | grep file-browser

# If multiple, stop all
docker-compose stop file-browser

# Start fresh
docker-compose up -d file-browser
```

### Issue: Health check failing

**Check health status:**
```bash
docker inspect file-browser | grep -A 10 Health
```

**Test health endpoint:**
```bash
docker exec -it file-browser wget -O- http://localhost:80/health
```

**If health check broken:**
```yaml
# Temporarily disable in docker-compose.yml
healthcheck:
  disable: true
```

---

## Maintenance

### Backup Database

```bash
# Create backup
cp filebrowser.db backups/filebrowser-$(date +%Y%m%d).db

# Or automated daily backup
0 2 * * * cp filebrowser.db /path/to/backups/filebrowser-$(date +\%Y\%m\%d).db
```

### Update File Browser

```bash
# Pull latest image
docker-compose pull file-browser

# Restart with new image
docker-compose up -d file-browser

# Verify version
docker-compose logs file-browser | head -20
```

### Clean Up Old Previews

File Browser generates thumbnails and previews:

```bash
# Check size
docker exec -it file-browser du -sh /tmp

# Clean if needed
docker exec -it file-browser rm -rf /tmp/*
```

### Monitor Resource Usage

```bash
# Real-time stats
docker stats file-browser

# Expected usage:
# Memory: ~50-100MB
# CPU: <1%
```

---

## Configuration Reference

### Environment Variables

| Variable | Value | Description |
|----------|-------|-------------|
| PUID | 0 | User ID (root) |
| PGID | 0 | Group ID (root) |
| FB_NOAUTH | false | Authentication required |
| FB_DATABASE | /database/filebrowser.db | Database location |
| FB_ROOT | /srv | Root directory |
| FB_LOG | stdout | Log to Docker logs |

### Volume Mounts

| Host | Container | Description |
|------|-----------|-------------|
| workspace | /srv | Workspace files |
| ./filebrowser.db | /database/filebrowser.db | User database |
| ./filebrowser-config.json | /.filebrowser.json | Configuration |

### Ports

| Container | Host | Description |
|-----------|------|-------------|
| 80 | 8080 | Web UI (local) |
| 80 | - | Coolify proxy (production) |

---

## Advanced Configuration

### Read-Only Access for Specific User

1. Create user with limited permissions:
```json
{
  "perm": {
    "admin": false,
    "execute": false,
    "create": false,
    "rename": false,
    "modify": false,
    "delete": false,
    "share": false,
    "download": true
  }
}
```

### Custom Theme

Edit `filebrowser-config.json`:
```json
{
  "branding": {
    "name": "My Project Files",
    "theme": "dark",
    "color": "#2979ff"
  }
}
```

### Restrict to Subdirectory

Per-user scope:
```json
{
  "scope": "/srv/specific-project"
}
```

---

## Uninstalling

```bash
# Stop and remove service
docker-compose stop file-browser
docker-compose rm -f file-browser

# Remove data (optional)
rm filebrowser.db
rm filebrowser-config.json

# Remove from docker-compose.yml
# Delete file-browser service definition
```

---

## Support

**Documentation:** https://filebrowser.org/
**GitHub:** https://github.com/filebrowser/filebrowser
**Issues:** Report in project repository

---

**Last Updated:** February 10, 2026
**File Browser Version:** s6 (latest)
**Status:** Production-ready
