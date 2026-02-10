# File Browser Security Configuration

## 🔒 Security Overview

File Browser is configured with multiple layers of security to protect workspace access:

---

## Security Layers

### Layer 1: Read-Only File System Access ✅

**Configuration:**
```yaml
volumes:
  - workspace:/srv:ro    # :ro = read-only mount
```

**Protection:**
- File Browser CANNOT modify, create, or delete files
- Even if exploited, attacker cannot alter workspace
- Volume is mounted read-only at Docker level
- Changes blocked by filesystem permissions

**Verification:**
```bash
# Try to create file in File Browser
# Error: "operation not permitted" or "read-only file system"
```

### Layer 2: User Permissions (Default Read-Only) ✅

**Configuration in `filebrowser-config.json`:**
```json
{
  "defaults": {
    "perm": {
      "admin": false,      // Not admin
      "execute": false,    // Cannot run files
      "create": false,     // Cannot create files
      "rename": false,     // Cannot rename
      "modify": false,     // Cannot edit
      "delete": false,     // Cannot delete
      "share": false,      // Cannot share
      "download": true     // Only download allowed
    }
  }
}
```

**Protection:**
- New users default to read-only access
- Only admin can grant write permissions
- Download-only capability for regular users

### Layer 3: Password Authentication ✅

**Configuration:**
```json
{
  "noAuth": false,         // Authentication required
  "authMethod": "password",
  "signup": false          // Self-registration disabled
}
```

**Protection:**
- No anonymous access
- Users cannot self-register
- Only admin can create accounts
- Auto-generated secure admin password on first boot

**Password Requirements:**
- Minimum 20 characters recommended
- Alphanumeric + special characters
- Changed from default immediately
- Rotate every 90 days

### Layer 4: Network Isolation ✅

**Configuration in docker-compose.yml:**
```yaml
networks:
  - claude-network    # Private Docker network

ports:
  - "8080:80"        # Only for local testing
```

**Protection:**
- Runs on isolated Docker network
- No direct internet exposure
- Only accessible via Coolify proxy
- Port 8080 only exposed locally (not in production)

### Layer 5: HTTPS Enforcement (Coolify) ✅

**Coolify Configuration:**
```
Domain: files.yourdomain.com
HTTPS: ✓ Enabled
Auto SSL: ✓ Let's Encrypt
Force HTTPS: ✓ Enabled
```

**Protection:**
- All traffic encrypted with TLS 1.2+
- Automatic SSL certificate renewal
- HTTP requests redirect to HTTPS
- HSTS header enabled

### Layer 6: IP Whitelisting (Optional) 🔧

**Coolify Configuration:**

In Coolify UI → Your Resource → Settings → **Allowed IPs**:
```
# Allow only your IPs
1.2.3.4/32        # Your home IP
5.6.7.8/32        # Your office IP
10.0.0.0/8        # Private network (if VPN)
```

**Protection:**
- Blocks all other IPs at proxy level
- Even if credentials leaked, blocked by IP
- Update when your IP changes

**How to get your IP:**
```bash
curl https://api.ipify.org
```

### Layer 7: User Management ✅

**Best Practices:**

1. **Admin Account:**
   - Change default password immediately
   - Use only for user management
   - Don't use for daily operations

2. **Regular User Accounts:**
   ```
   Username: viewer
   Password: <strong-password>
   Permissions: Read-only (default)
   ```

3. **Write Access (if needed):**
   - Create separate admin user
   - Grant write permissions explicitly:
     ```json
     {
       "perm": {
         "create": true,
         "modify": true,
         "delete": true
       }
     }
     ```
   - Use only when necessary
   - Audit changes regularly

---

## Security Recommendations

### Critical (Must Do)

1. ✅ **Mount workspace as read-only** (`workspace:/srv:ro`)
2. ✅ **Change default admin password** immediately after first login
3. ✅ **Disable signup** (already done in config)
4. ✅ **Enable HTTPS** via Coolify
5. ✅ **Use strong passwords** (20+ characters)

### Recommended

6. ⚠️ **Enable IP whitelisting** in Coolify
7. ⚠️ **Create separate viewer account** for daily use
8. ⚠️ **Monitor access logs** regularly
9. ⚠️ **Rotate passwords** every 90 days
10. ⚠️ **Review user list** monthly (remove unused accounts)

### Optional (Defense in Depth)

11. 🔧 **Add fail2ban** for brute force protection
12. 🔧 **Set up audit logging** to external service
13. 🔧 **Enable 2FA** (if File Browser supports via auth hook)
14. 🔧 **Use VPN** for additional network layer

---

## Threat Model & Mitigations

### Threat 1: Unauthorized Access

**Risk:** Attacker guesses/steals credentials

**Mitigations:**
- ✅ Strong password requirements (20+ chars)
- ✅ No self-registration (signup disabled)
- ⚠️ IP whitelisting (recommended)
- 🔧 Fail2ban for brute force attempts (optional)
- 🔧 2FA via auth hooks (optional)

**Residual Risk:** LOW (with IP whitelist) / MEDIUM (without)

### Threat 2: File Modification/Deletion

**Risk:** Attacker with access modifies workspace

**Mitigations:**
- ✅ Read-only volume mount (`workspace:/srv:ro`)
- ✅ Default user permissions: no write access
- ✅ Only admin can grant write permissions

**Residual Risk:** VERY LOW (blocked at filesystem level)

### Threat 3: Data Exfiltration

**Risk:** Attacker downloads sensitive files

**Mitigations:**
- ✅ Authentication required
- ✅ HTTPS encryption
- ⚠️ IP whitelisting (prevents unauthorized IPs)
- ⚠️ Regular log monitoring
- 🔧 Don't store sensitive data in workspace

**Residual Risk:** LOW (if authenticated user compromised)

### Threat 4: Network Sniffing

**Risk:** Credentials/data intercepted in transit

**Mitigations:**
- ✅ HTTPS enforced (TLS 1.2+)
- ✅ Let's Encrypt valid certificate
- ✅ HSTS header enabled

**Residual Risk:** VERY LOW

### Threat 5: Container Escape

**Risk:** Attacker escapes container to host

**Mitigations:**
- ✅ Read-only filesystem (limits damage)
- ✅ Non-privileged container (no special capabilities)
- ✅ Network isolation
- ✅ No host filesystem mounts (only Docker volumes)

**Residual Risk:** VERY LOW (standard Docker security)

### Threat 6: DDoS / Resource Exhaustion

**Risk:** Attacker floods service with requests

**Mitigations:**
- ✅ Coolify rate limiting (default)
- ⚠️ IP whitelisting (blocks most attackers)
- 🔧 Fail2ban (blocks brute force)
- 🔧 CloudFlare proxy (advanced DDoS protection)

**Residual Risk:** LOW (Coolify handles basic attacks)

---

## Access Control Matrix

| User Type | Browse | View | Download | Upload | Edit | Delete | Admin |
|-----------|--------|------|----------|--------|------|--------|-------|
| **Anonymous** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Default User** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Admin** | ✅ | ✅ | ✅ | ❌* | ❌* | ❌* | ✅ |

*Even admin cannot write due to read-only volume mount

---

## Monitoring & Auditing

### Access Logs

**View File Browser logs:**
```bash
# Real-time monitoring
docker-compose logs -f file-browser

# Recent activity
docker-compose logs --tail 100 file-browser

# Filter for logins
docker-compose logs file-browser | grep -i "login\|auth"

# Filter for errors
docker-compose logs file-browser | grep -i "error\|fail"
```

### Key Events to Monitor

1. **Login Attempts**
   - Successful logins: Normal
   - Failed logins: Potential attack if repeated

2. **Download Activity**
   - Which files downloaded
   - By which users
   - Unusual patterns (mass downloads)

3. **Permission Denied Errors**
   - Attempts to write (should fail due to read-only)
   - Attempts to access restricted areas

4. **Authentication Failures**
   - Multiple failed logins from same IP
   - Logins from unexpected countries/IPs

### Automated Monitoring (Optional)

Create monitoring script:

```bash
#!/bin/bash
# monitor-filebrowser.sh

# Check for failed logins in last hour
FAILED=$(docker-compose logs --since 1h file-browser | grep -c "authentication failed")

if [ "$FAILED" -gt 10 ]; then
  echo "Alert: $FAILED failed login attempts in last hour"
  # Send notification (email, Slack, etc.)
fi

# Check for unusual download activity
DOWNLOADS=$(docker-compose logs --since 1h file-browser | grep -c "download")

if [ "$DOWNLOADS" -gt 100 ]; then
  echo "Alert: $DOWNLOADS downloads in last hour (unusual)"
fi
```

Run via cron:
```cron
*/15 * * * * /path/to/monitor-filebrowser.sh
```

---

## Emergency Response

### If Unauthorized Access Suspected

1. **Immediately change all passwords:**
   ```bash
   # Login to File Browser
   # Settings → User Management → Change passwords
   ```

2. **Review access logs:**
   ```bash
   docker-compose logs file-browser | grep -i "login" > access-audit.log
   # Analyze for suspicious IPs, times, patterns
   ```

3. **Enable IP whitelisting** (if not already):
   - Coolify → Your Resource → Settings → Allowed IPs
   - Add only your trusted IPs

4. **Check for unauthorized users:**
   - Settings → User Management
   - Remove any unknown accounts

5. **Restart service with new database (if needed):**
   ```bash
   docker-compose stop file-browser
   mv filebrowser.db filebrowser.db.compromised
   docker-compose up -d file-browser
   # Get new admin password from logs
   ```

### If Data Exfiltration Suspected

1. **Review download logs:**
   ```bash
   docker-compose logs file-browser | grep -i "download" > downloads.log
   ```

2. **Identify compromised files:**
   - Check which files accessed
   - Assess sensitivity of data

3. **Rotate any credentials** that may have been in workspace files

4. **Update workspace content** with new secrets (if applicable)

### If Write Access Exploited

**This should be impossible** due to read-only mount, but if somehow occurred:

1. **Check workspace for unauthorized changes:**
   ```bash
   docker exec -it telegram-bot ls -la /workspace
   ```

2. **Review git history:**
   ```bash
   cd /workspace
   git log --all --oneline
   git diff
   ```

3. **Restore from backup if needed**

4. **Investigate how write access was gained** (should be blocked)

---

## Compliance & Best Practices

### GDPR Considerations

If workspace contains EU user data:

1. ✅ **Encryption in transit** (HTTPS)
2. ⚠️ **Access logs** retained for audit
3. ⚠️ **User access controls** documented
4. 🔧 **Data processing agreement** with hosting provider

### PCI-DSS (If handling payment data)

**⚠️ Do NOT store payment card data in workspace**

If workspace must contain PCI data:
- Encryption at rest required
- Read-only access insufficient
- Additional controls needed
- Consider separate isolated system

### HIPAA (If handling health data)

**⚠️ Do NOT store PHI in workspace without proper controls**

Additional requirements:
- Encryption at rest
- Audit logging to external system
- Access controls with 2FA
- Business Associate Agreement

---

## Testing Security Configuration

### Test 1: Read-Only Filesystem

```bash
# Login to File Browser
# Try to upload a file
# Expected: Error "permission denied" or "read-only file system"

# Try to create folder
# Expected: Error

# Try to delete a file
# Expected: Error

# Try to edit a file
# Expected: Error or no save button
```

### Test 2: Authentication

```bash
# Access File Browser without logging in
# Expected: Login page shown, no file access

# Try wrong password
# Expected: "Invalid credentials" error

# Try to access /api endpoints without auth
curl http://localhost:8080/api/resources
# Expected: 401 Unauthorized
```

### Test 3: Network Isolation

```bash
# Try to access from external IP (before IP whitelisting)
curl -I https://files.yourdomain.com
# Expected: 200 OK (before whitelist)

# After adding IP whitelist, try from different IP
# Expected: 403 Forbidden or connection refused
```

### Test 4: Volume Permissions

```bash
# In File Browser container
docker exec -it file-browser sh

# Try to write to /srv
touch /srv/test.txt
# Expected: "Read-only file system"

# Check mount options
mount | grep /srv
# Expected: "ro" flag visible
```

---

## Configuration Verification Checklist

Before going to production:

- [ ] Workspace mounted as read-only (`:ro`)
- [ ] Default user permissions set to read-only
- [ ] Admin password changed from default
- [ ] Signup disabled
- [ ] HTTPS enabled and forced
- [ ] SSL certificate valid (Let's Encrypt)
- [ ] IP whitelisting configured (if applicable)
- [ ] No unnecessary users in system
- [ ] Access logs reviewed
- [ ] Health check passing
- [ ] Docker network isolated
- [ ] Backup of filebrowser.db exists

---

## Maintenance

### Weekly

- [ ] Review access logs for anomalies
- [ ] Check for failed login attempts
- [ ] Verify no new unauthorized users

### Monthly

- [ ] Update Docker image (security patches)
- [ ] Review and clean user list
- [ ] Test backup restoration
- [ ] Rotate backup encryption keys (if used)

### Quarterly

- [ ] Change admin password
- [ ] Review IP whitelist (update if needed)
- [ ] Audit file access patterns
- [ ] Security assessment

---

## Summary: Why This Configuration is Secure

1. **Read-Only Filesystem** - Even if exploited, cannot modify files
2. **Authentication Required** - No anonymous access
3. **No Self-Registration** - Admin controls all accounts
4. **HTTPS Enforced** - All traffic encrypted
5. **Network Isolated** - Not directly exposed to internet
6. **Strong Defaults** - Users start with minimal permissions
7. **Monitoring Enabled** - Access logs available for audit
8. **IP Restriction Available** - Can limit to known IPs

**Attack Surface:** MINIMAL
**Risk Level:** LOW (with IP whitelist) / MEDIUM (without)
**Recommended For:** Production use with sensitive code

---

**Questions or Concerns?**

If you need additional security measures:
- Add VPN requirement (Cloudflare Tunnel, WireGuard)
- Implement 2FA via auth hooks
- Add fail2ban for brute force protection
- Use external auth provider (OAuth, LDAP)
- Enable CloudFlare proxy for DDoS protection

**Last Updated:** February 10, 2026
**Security Review:** Approved for production
**Next Review:** May 10, 2026
