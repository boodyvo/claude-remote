# Web UI Options for File System & Claude Code Access

**Date:** February 10, 2026
**Purpose:** Evaluate and implement web-based UI for accessing workspace filesystem and Claude Code environment

---

## Overview

This document evaluates options for web-based access to the workspace filesystem where Claude Code operates, allowing users to browse files, edit code, and monitor the environment through a browser interface.

## Requirements

- Browse and navigate workspace filesystem
- View and edit code files with syntax highlighting
- Access from any device (desktop, mobile, tablet)
- Secure authentication
- Easy Docker deployment
- Works with existing docker-compose setup
- Low resource overhead

---

## Option 1: File Browser (Recommended) ⭐

**Image:** `filebrowser/filebrowser:latest`
**Port:** 8080
**Size:** ~30MB
**Popularity:** 26k+ stars on GitHub

### Description
File Browser is a lightweight, dedicated file management web application. It provides a clean, modern interface for browsing, uploading, downloading, and editing files through a web browser.

### Pros
✅ Very lightweight (~30MB image)
✅ Simple, focused on file operations
✅ Excellent mobile support
✅ Built-in authentication and user management
✅ File sharing with password protection
✅ Preview support (images, videos, PDFs, markdown)
✅ Basic text editor with syntax highlighting
✅ Easy Docker setup (one service)
✅ Low resource usage
✅ Search functionality

### Cons
❌ Not a full IDE (limited code editing features)
❌ No terminal access
❌ No git integration
❌ Basic editor (not as feature-rich as VSCode)

### Docker Configuration

```yaml
file-browser:
  image: filebrowser/filebrowser:latest
  container_name: file-browser

  environment:
    - PUID=1000
    - PGID=1000

  volumes:
    - workspace:/srv
    - ./filebrowser.db:/database/filebrowser.db
    - ./filebrowser.json:/config/settings.json

  ports:
    - "8080:80"

  restart: unless-stopped

  networks:
    - claude-network
```

### Setup Steps

1. **Add service to docker-compose.yml**
2. **Create config file** (`filebrowser.json`):
   ```json
   {
     "port": 80,
     "baseURL": "",
     "address": "",
     "log": "stdout",
     "database": "/database/filebrowser.db",
     "root": "/srv"
   }
   ```
3. **Deploy:** `docker-compose up -d file-browser`
4. **Access:** `https://your-domain.com` (behind Coolify proxy)
5. **Default credentials:** admin/admin (change immediately)

### Coolify Integration

Add domain in Coolify:
- Service: file-browser
- Domain: `files.yourdomain.com`
- Port: 80 (internal)
- HTTPS: ✓ Enabled

### Use Cases
- Quick file browsing
- Upload/download files
- Edit configuration files
- View logs
- Share files with team members
- Mobile file access

### Estimated Resource Usage
- Memory: ~50MB
- CPU: <1%
- Disk: ~30MB (image)

---

## Option 2: Code-Server (VSCode in Browser)

**Image:** `linuxserver/code-server:latest`
**Port:** 8443
**Size:** ~1.5GB
**Popularity:** 68k+ stars on GitHub (upstream VSCode)

### Description
Code-Server runs Visual Studio Code in the browser, providing a full-featured IDE experience with extensions, terminal, git integration, and all VSCode functionality.

### Pros
✅ Full VSCode experience in browser
✅ Terminal access (can run `claude` commands)
✅ Git integration built-in
✅ Extension marketplace support
✅ Multi-language support
✅ Excellent syntax highlighting and IntelliSense
✅ Split panes, search & replace
✅ Debugging capabilities
✅ Well-maintained by LinuxServer.io

### Cons
❌ Large image size (~1.5GB)
❌ Higher resource usage (500MB+ RAM)
❌ Slower startup time
❌ More complex configuration
❌ Overkill if only need file browsing

### Docker Configuration

```yaml
code-server:
  image: linuxserver/code-server:latest
  container_name: code-server

  environment:
    - PUID=1000
    - PGID=1000
    - TZ=Etc/UTC
    - PASSWORD=${CODE_SERVER_PASSWORD}
    - SUDO_PASSWORD=${CODE_SERVER_SUDO_PASSWORD}
    - DEFAULT_WORKSPACE=/workspace

  volumes:
    - ./code-server-config:/config
    - workspace:/workspace
    - claude-config:/root/.claude

  ports:
    - "8443:8443"

  restart: unless-stopped

  networks:
    - claude-network
```

### Setup Steps

1. **Add service to docker-compose.yml**
2. **Set passwords in .env:**
   ```env
   CODE_SERVER_PASSWORD=your-secure-password
   CODE_SERVER_SUDO_PASSWORD=your-sudo-password
   ```
3. **Deploy:** `docker-compose up -d code-server`
4. **Access:** `https://code.yourdomain.com`
5. **Install Claude Code extension** (if available) or use terminal

### Coolify Integration

Add domain in Coolify:
- Service: code-server
- Domain: `code.yourdomain.com`
- Port: 8443 (internal)
- HTTPS: ✓ Enabled

### Use Cases
- Full development environment
- Run Claude Code directly in browser
- Debug applications
- Work from iPad/Chromebook
- Complex refactoring tasks
- Multi-file editing

### Estimated Resource Usage
- Memory: 500MB - 1GB
- CPU: 5-10%
- Disk: ~1.5GB (image) + config

---

## Option 3: WeTTy + File Browser (Hybrid)

**Images:**
- `wettyoss/wetty:latest` (Terminal)
- `filebrowser/filebrowser:latest` (Files)

**Ports:** 3000 (terminal), 8080 (files)
**Combined Size:** ~60MB
**Approach:** Best of both worlds

### Description
Combine WeTTy (web-based terminal) with File Browser to get both terminal access and file management in separate, lightweight services.

### Pros
✅ Lightweight (combined <100MB)
✅ Terminal access for `claude` commands
✅ File browsing and editing
✅ Two focused tools (do one thing well)
✅ Low resource usage
✅ Can use independently
✅ SSH access to container

### Cons
❌ Two separate interfaces
❌ Not integrated (switch between tabs)
❌ Requires 2 services instead of 1
❌ Terminal experience not as rich as VSCode

### Docker Configuration

```yaml
# Web Terminal
wetty:
  image: wettyoss/wetty:latest
  container_name: wetty-terminal

  command: --ssh-host=telegram-bot --ssh-port=22

  environment:
    - SSHHOST=telegram-bot
    - SSHPORT=22

  ports:
    - "3000:3000"

  restart: unless-stopped

  networks:
    - claude-network

# File Browser (same as Option 1)
file-browser:
  image: filebrowser/filebrowser:latest
  # ... (configuration from Option 1)
```

**Note:** Requires SSH server in telegram-bot container.

### Setup Steps

1. **Add OpenSSH to bot/Dockerfile:**
   ```dockerfile
   RUN apt-get update && apt-get install -y openssh-server
   RUN mkdir /var/run/sshd
   RUN echo 'root:your-password' | chpasswd
   CMD service ssh start && python bot.py
   ```

2. **Add both services to docker-compose.yml**
3. **Deploy:** `docker-compose up -d wetty file-browser`
4. **Access:**
   - Terminal: `https://terminal.yourdomain.com`
   - Files: `https://files.yourdomain.com`

### Use Cases
- Run `claude` commands via web terminal
- Browse/edit files in separate window
- Quick SSH access from browser
- Lightweight development environment

### Estimated Resource Usage
- Memory: ~100MB (both services)
- CPU: 1-2%
- Disk: ~60MB (both images)

---

## Comparison Matrix

| Feature | File Browser | Code-Server | WeTTy + File Browser |
|---------|-------------|-------------|---------------------|
| **Image Size** | 30MB | 1.5GB | 60MB |
| **Memory Usage** | 50MB | 500MB-1GB | 100MB |
| **File Browsing** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Code Editing** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Terminal Access** | ❌ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Mobile Support** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Setup Complexity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Resource Efficiency** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Git Integration** | ❌ | ⭐⭐⭐⭐⭐ | ❌ |
| **Authentication** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## Recommendation: File Browser ⭐

**Choose File Browser for this project because:**

1. **Lightweight** - 30MB vs 1.5GB (Code-Server)
2. **Purpose-built** - Designed specifically for file management
3. **Mobile-friendly** - Best responsive design
4. **Low overhead** - Won't impact bot performance
5. **Simple setup** - Single service, minimal config
6. **Sufficient features** - Covers 90% of use cases
7. **Quick access** - Fast to browse files and check logs
8. **Secure** - Built-in auth, user management

**When to use alternatives:**

- **Code-Server:** If you need full IDE features, debugging, or spend significant time coding in the environment
- **WeTTy + File Browser:** If you frequently need to run `claude` commands directly but want minimal overhead

---

## Implementation Plan

### Phase 1: File Browser Setup (Recommended - 20 minutes)

#### Step 1: Update docker-compose.yml

Add File Browser service:

```yaml
services:
  # ... existing telegram-bot service ...

  # ==================================================
  # File Browser - Web-based File Manager
  # ==================================================
  file-browser:
    image: filebrowser/filebrowser:latest
    container_name: file-browser

    environment:
      - PUID=1000
      - PGID=1000

    volumes:
      - workspace:/srv                    # Workspace files
      - ./filebrowser.db:/database/filebrowser.db
      - ./filebrowser-config:/config

    ports:
      - "8080:80"

    healthcheck:
      test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:80 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3

    restart: unless-stopped

    networks:
      - claude-network

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### Step 2: Create Configuration Directory

```bash
mkdir -p filebrowser-config
```

Optional: Create `filebrowser-config/settings.json`:

```json
{
  "port": 80,
  "baseURL": "",
  "address": "",
  "log": "stdout",
  "database": "/database/filebrowser.db",
  "root": "/srv",
  "signup": false,
  "authMethod": "password"
}
```

#### Step 3: Deploy Locally (Test)

```bash
# Test locally first
docker-compose up -d file-browser

# Check logs
docker-compose logs -f file-browser

# Access at http://localhost:8080
# Default login: admin / admin
```

#### Step 4: Change Default Password

1. Login with admin/admin
2. Go to Settings → User Management
3. Change admin password
4. Create additional users if needed

#### Step 5: Configure in Coolify

In Coolify UI:

1. **Add Domain:**
   - Go to your resource → Domains
   - Add: `files.yourdomain.com`
   - Map to service: file-browser
   - Internal port: 80
   - Enable HTTPS + Force HTTPS

2. **DNS Configuration:**
   ```
   Type: A
   Name: files
   Value: <your-server-ip>
   ```

3. **Verify:**
   ```bash
   dig files.yourdomain.com
   ```

#### Step 6: Commit & Deploy

```bash
git add docker-compose.yml filebrowser-config/
git commit -m "Add File Browser for web-based file management"
git push origin main
```

Coolify will auto-deploy if webhooks are configured.

#### Step 7: Test Production

1. Access `https://files.yourdomain.com`
2. Login with your credentials
3. Browse `/workspace` directory
4. Test file upload/download
5. Edit a file (e.g., README.md)

#### Step 8: Update Documentation

Update README.md and COOLIFY_DEPLOY.md to include File Browser setup.

### Expected Results

✅ Web UI accessible at `https://files.yourdomain.com`
✅ Can browse workspace filesystem
✅ Can view and edit files
✅ Can upload/download files
✅ Mobile-friendly interface
✅ Secure with authentication
✅ Low resource overhead

---

### Phase 2: Alternative - Code-Server Setup (Optional - 30 minutes)

**Only implement if you need full IDE features.**

#### Prerequisites
- At least 2GB RAM available
- 2GB free disk space

#### Step 1: Add Environment Variables

In `.env.example` and your `.env`:

```env
# Code-Server Configuration (Optional)
CODE_SERVER_PASSWORD=your-secure-password
CODE_SERVER_SUDO_PASSWORD=your-sudo-password
```

#### Step 2: Update docker-compose.yml

```yaml
  code-server:
    image: linuxserver/code-server:latest
    container_name: code-server

    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
      - PASSWORD=${CODE_SERVER_PASSWORD:?Code-Server password required}
      - SUDO_PASSWORD=${CODE_SERVER_SUDO_PASSWORD:-}
      - DEFAULT_WORKSPACE=/workspace

    volumes:
      - ./code-server-config:/config
      - workspace:/workspace
      - claude-config:/root/.claude

    ports:
      - "8443:8443"

    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8443 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

    restart: unless-stopped

    networks:
      - claude-network

    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### Step 3: Deploy & Configure

```bash
mkdir -p code-server-config
docker-compose up -d code-server
```

#### Step 4: Add Domain in Coolify

- Domain: `code.yourdomain.com`
- Service: code-server
- Port: 8443

#### Step 5: Install Extensions (Optional)

Once logged in to Code-Server:
1. Open Extensions panel (Ctrl+Shift+X)
2. Search and install:
   - Python
   - GitLens
   - Docker
   - Markdown All in One

---

## Security Considerations

### File Browser
- Change default admin password immediately
- Disable signup if not needed
- Use strong passwords (20+ characters)
- Enable HTTPS (handled by Coolify)
- Limit user permissions appropriately
- Regular password rotation

### Code-Server
- Use strong PASSWORD and SUDO_PASSWORD
- Never expose port directly (use Coolify proxy)
- Enable 2FA if available
- Review installed extensions
- Keep image updated

### General
- All web UIs should be behind Coolify's Traefik proxy
- HTTPS only (no HTTP access)
- Consider adding IP whitelist in Coolify
- Monitor access logs
- Update Docker images regularly

---

## Maintenance

### File Browser
```bash
# Update to latest version
docker-compose pull file-browser
docker-compose up -d file-browser

# Backup database
cp filebrowser.db filebrowser.db.backup

# View logs
docker-compose logs -f file-browser

# Restart if needed
docker-compose restart file-browser
```

### Code-Server
```bash
# Update
docker-compose pull code-server
docker-compose up -d code-server

# Backup config
tar -czf code-server-config-backup.tar.gz code-server-config/

# Check resource usage
docker stats code-server
```

---

## Cost Impact

### File Browser (Recommended)
- **Server:** No additional cost (same VPS)
- **Storage:** ~100MB (image + database)
- **Memory:** ~50MB RAM
- **Total:** $0/month additional

### Code-Server
- **Server:** May need VPS upgrade (+€5/month if RAM limited)
- **Storage:** ~2GB
- **Memory:** ~500MB-1GB RAM
- **Total:** $0-5/month

---

## Troubleshooting

### File Browser

**Issue:** Can't access web UI
```bash
# Check service is running
docker-compose ps file-browser

# Check logs for errors
docker-compose logs file-browser

# Verify port binding
netstat -tulpn | grep 8080
```

**Issue:** Permission denied when editing files
```bash
# Fix permissions on workspace
docker exec -it file-browser chown -R 1000:1000 /srv
```

**Issue:** Forgot admin password
```bash
# Reset to defaults
docker exec -it file-browser rm /database/filebrowser.db
docker-compose restart file-browser
# Login with admin/admin, then change password
```

### Code-Server

**Issue:** High memory usage
```bash
# Check stats
docker stats code-server

# Restart service
docker-compose restart code-server

# Consider upgrading VPS if persistent
```

**Issue:** Can't run terminal commands
- Verify workspace volume is mounted
- Check user permissions (PUID/PGID)
- Ensure SUDO_PASSWORD is set for sudo access

---

## Conclusion

**Recommended Implementation:**

1. **Start with File Browser** (Phase 1)
   - Quick setup (20 minutes)
   - Low resource usage
   - Covers 90% of needs
   - Mobile-friendly

2. **Add Code-Server later** (Phase 2 - Optional)
   - Only if you need full IDE
   - Requires more resources
   - Better for heavy development work

3. **Monitor usage:**
   - If you rarely use web UI → File Browser is perfect
   - If you code extensively in browser → Add Code-Server
   - If you need terminal often → Consider WeTTy

**Next Steps:**
1. Review this plan
2. Implement Phase 1 (File Browser)
3. Test functionality
4. Evaluate if Phase 2 (Code-Server) is needed

---

**Status:** Ready for implementation
**Estimated Time:** 20 minutes (File Browser) or 30 minutes (Code-Server)
**Impact:** Low (lightweight) to Medium (Code-Server)
**Priority:** Optional enhancement (bot works without it)
