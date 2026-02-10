# Step 24: Security Hardening

**Estimated Time:** 30 minutes
**Phase:** 6 - Monitoring, Backup & Optimization
**Prerequisites:** Performance optimization complete (Step 23)

---

## Overview

This step implements comprehensive security hardening for the claude-remote-runner system. It covers access controls, API key security, network security, input validation, and security monitoring. The goal is to protect against common threats while maintaining usability.

### Context

Security is critical for a production system that:
- Executes arbitrary commands via Claude Code
- Has access to your files and git repositories
- Handles API keys worth hundreds of dollars
- Processes voice input from external sources
- Runs 24/7 on a public server

### Goals

- Implement multi-layer access controls
- Secure API keys and credentials
- Harden network configuration
- Add input validation and sanitization
- Implement security monitoring
- Document security best practices
- Pass security audit checklist

---

## Implementation Details

### 1. Access Control Hardening

#### 1.1 Telegram User Authentication

Enhance the existing user authorization:

**bot/auth.py:**

```python
"""
Enhanced authentication and authorization for Telegram bot.
"""

import os
import logging
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class UserPermissions:
    """User permission levels."""
    can_execute_commands: bool = True
    can_modify_files: bool = True
    can_use_git: bool = True
    is_admin: bool = False
    rate_limit_multiplier: float = 1.0


class AuthManager:
    """Manage user authentication and authorization."""

    def __init__(self):
        # Load allowed users from environment
        self.allowed_user_ids = self._parse_allowed_users()
        self.admin_user_ids = self._parse_admin_users()

        # Track login attempts for security monitoring
        self.login_attempts = {}
        self.blocked_users = set()

    def _parse_allowed_users(self) -> List[int]:
        """Parse ALLOWED_USER_IDS from environment."""
        user_ids_str = os.environ.get('ALLOWED_USER_IDS', '')
        if not user_ids_str:
            logger.warning("⚠️  ALLOWED_USER_IDS not set - bot is open to all users!")
            return []

        try:
            user_ids = [int(uid.strip()) for uid in user_ids_str.split(',') if uid.strip()]
            logger.info(f"Allowed users: {len(user_ids)} user(s)")
            return user_ids
        except ValueError as e:
            logger.error(f"Error parsing ALLOWED_USER_IDS: {e}")
            return []

    def _parse_admin_users(self) -> List[int]:
        """Parse ADMIN_USER_IDS from environment."""
        admin_ids_str = os.environ.get('ADMIN_USER_IDS', '')
        if not admin_ids_str:
            return []

        try:
            admin_ids = [int(uid.strip()) for uid in admin_ids_str.split(',') if uid.strip()]
            logger.info(f"Admin users: {len(admin_ids)} user(s)")
            return admin_ids
        except ValueError as e:
            logger.error(f"Error parsing ADMIN_USER_IDS: {e}")
            return []

    def is_authorized(self, user_id: int, username: Optional[str] = None) -> bool:
        """Check if user is authorized to use the bot."""
        # If no restrictions configured, allow all (dev mode)
        if not self.allowed_user_ids:
            logger.warning(f"Allowing user {user_id} (@{username}) - no restrictions configured")
            return True

        # Check if user is blocked
        if user_id in self.blocked_users:
            logger.warning(f"Blocked user attempted access: {user_id} (@{username})")
            return False

        # Check whitelist
        is_allowed = user_id in self.allowed_user_ids
        if not is_allowed:
            logger.warning(f"Unauthorized access attempt: {user_id} (@{username})")
            self._record_failed_attempt(user_id)

        return is_allowed

    def get_permissions(self, user_id: int) -> UserPermissions:
        """Get permissions for a user."""
        is_admin = user_id in self.admin_user_ids

        return UserPermissions(
            can_execute_commands=True,
            can_modify_files=True,
            can_use_git=True,
            is_admin=is_admin,
            rate_limit_multiplier=2.0 if is_admin else 1.0
        )

    def _record_failed_attempt(self, user_id: int):
        """Record failed authentication attempt."""
        if user_id not in self.login_attempts:
            self.login_attempts[user_id] = []

        self.login_attempts[user_id].append(datetime.now())

        # Block user after 5 failed attempts
        if len(self.login_attempts[user_id]) >= 5:
            self.blocked_users.add(user_id)
            logger.error(f"🚨 User {user_id} blocked after 5 failed attempts")

    def unblock_user(self, user_id: int):
        """Admin function to unblock a user."""
        if user_id in self.blocked_users:
            self.blocked_users.remove(user_id)
            self.login_attempts.pop(user_id, None)
            logger.info(f"User {user_id} unblocked")


# Global auth manager
auth_manager = AuthManager()
```

#### 1.2 Web UI Basic Auth Enhancement

Update environment variables in `.env`:

```env
# Web UI Authentication (REQUIRED for production)
BASIC_AUTH_USER=admin
BASIC_AUTH_PASS=your-strong-password-min-16-chars

# Change default credentials immediately after first deployment!
```

**Password Requirements:**
- Minimum 16 characters
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words
- Use password generator

**Generate strong password:**

```bash
# Method 1: OpenSSL
openssl rand -base64 24

# Method 2: Python
python3 -c "import secrets; print(secrets.token_urlsafe(24))"

# Method 3: pwgen (if installed)
pwgen -s 24 1
```

#### 1.3 Admin Commands

Add admin-only commands to **bot/bot.py**:

```python
from auth import auth_manager

async def handle_admin_stats(update: Update, context):
    """Show system statistics (admin only)."""
    user_id = update.effective_user.id
    permissions = auth_manager.get_permissions(user_id)

    if not permissions.is_admin:
        await update.message.reply_text("⛔ Admin access required")
        return

    stats = {
        'authorized_users': len(auth_manager.allowed_user_ids),
        'admin_users': len(auth_manager.admin_user_ids),
        'failed_attempts': sum(len(attempts) for attempts in auth_manager.login_attempts.values()),
        'blocked_users': len(auth_manager.blocked_users),
        'uptime': get_uptime(),
        'memory_usage': get_memory_usage(),
    }

    message = "🔐 **System Statistics (Admin)**\n\n"
    for key, value in stats.items():
        message += f"**{key.replace('_', ' ').title()}:** {value}\n"

    await update.message.reply_text(message, parse_mode='Markdown')


async def handle_admin_unblock(update: Update, context):
    """Unblock a user (admin only)."""
    user_id = update.effective_user.id
    permissions = auth_manager.get_permissions(user_id)

    if not permissions.is_admin:
        await update.message.reply_text("⛔ Admin access required")
        return

    if not context.args:
        await update.message.reply_text("Usage: /unblock <user_id>")
        return

    try:
        target_user_id = int(context.args[0])
        auth_manager.unblock_user(target_user_id)
        await update.message.reply_text(f"✅ User {target_user_id} unblocked")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID")


# Register admin commands
app.add_handler(CommandHandler("adminstats", handle_admin_stats))
app.add_handler(CommandHandler("unblock", handle_admin_unblock))
```

### 2. API Key Security

#### 2.1 Environment Variable Security

**Critical Security Practices:**

```bash
# ✅ DO: Use Coolify's encrypted environment variables
# Configure in Coolify UI, mark as "Secret"

# ✅ DO: Rotate API keys every 90 days
# Set calendar reminder

# ✅ DO: Use separate keys for dev/prod
# Never use production keys in development

# ❌ DON'T: Commit .env to git
# Verify .gitignore includes .env

# ❌ DON'T: Share API keys in logs
# Sanitize logs before sharing

# ❌ DON'T: Use API keys in URLs
# Always use headers for authentication
```

#### 2.2 Log Sanitization

Add log sanitization to prevent API key leakage:

**bot/utils.py:**

```python
"""
Utility functions including log sanitization.
"""

import re
import logging

# Patterns to redact from logs
SENSITIVE_PATTERNS = [
    (re.compile(r'sk-ant-api03-[A-Za-z0-9_-]+'), 'sk-ant-api03-***REDACTED***'),
    (re.compile(r'sk-[A-Za-z0-9]{48}'), 'sk-***REDACTED***'),  # OpenAI key
    (re.compile(r'\d{10}:[A-Za-z0-9_-]{35}'), '***REDACTED_TOKEN***'),  # Telegram token
    (re.compile(r'Bearer [A-Za-z0-9_-]+'), 'Bearer ***REDACTED***'),
    (re.compile(r'"api_key":\s*"[^"]+"'), '"api_key": "***REDACTED***"'),
    (re.compile(r'"password":\s*"[^"]+"'), '"password": "***REDACTED***"'),
]


class SanitizingFormatter(logging.Formatter):
    """Logging formatter that redacts sensitive information."""

    def format(self, record):
        message = super().format(record)

        # Redact sensitive patterns
        for pattern, replacement in SENSITIVE_PATTERNS:
            message = pattern.sub(replacement, message)

        return message


def setup_secure_logging():
    """Configure logging with sanitization."""
    handler = logging.StreamHandler()
    handler.setFormatter(SanitizingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(logging.INFO)
```

Update **bot/bot.py**:

```python
from utils import setup_secure_logging

# Replace existing logging config with:
setup_secure_logging()
logger = logging.getLogger(__name__)
```

### 3. Input Validation & Sanitization

#### 3.1 Voice/Text Input Validation

Add input validation to prevent injection attacks:

**bot/validators.py:**

```python
"""
Input validation and sanitization.
"""

import re
from typing import Tuple

# Maximum input lengths
MAX_TEXT_LENGTH = 2000
MAX_VOICE_DURATION = 120  # seconds

# Dangerous command patterns (block these)
DANGEROUS_PATTERNS = [
    re.compile(r'rm\s+-rf\s+/'),  # Dangerous deletions
    re.compile(r':\(\)\{.*\}'),    # Fork bombs
    re.compile(r'eval\s*\('),      # Code injection
    re.compile(r'exec\s*\('),      # Code execution
    re.compile(r'__import__'),     # Dynamic imports
    re.compile(r'subprocess\.'),   # Subprocess calls
    re.compile(r'os\.system'),     # System calls
]


def validate_text_input(text: str) -> Tuple[bool, str]:
    """
    Validate user text input.

    Returns:
        (is_valid: bool, error_message: str)
    """
    # Check length
    if len(text) > MAX_TEXT_LENGTH:
        return False, f"⚠️ Input too long (max {MAX_TEXT_LENGTH} characters)"

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(text):
            return False, "🚨 Potentially dangerous command detected and blocked"

    # Check for excessive special characters (possible injection)
    special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
    if special_char_ratio > 0.5:
        return False, "⚠️ Input contains too many special characters"

    return True, ""


def validate_voice_duration(duration: int) -> Tuple[bool, str]:
    """
    Validate voice message duration.

    Returns:
        (is_valid: bool, error_message: str)
    """
    if duration > MAX_VOICE_DURATION:
        return False, f"⚠️ Voice message too long (max {MAX_VOICE_DURATION} seconds)"

    if duration < 1:
        return False, "⚠️ Voice message too short"

    return True, ""


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal.

    Example:
        sanitize_filename("../../etc/passwd") -> "passwd"
    """
    # Remove directory components
    filename = filename.split('/')[-1]

    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename
```

Update handlers in **bot/bot.py**:

```python
from validators import validate_text_input, validate_voice_duration

async def handle_text(update: Update, context):
    """Handle text messages with validation."""
    user_id = update.effective_user.id
    text = update.message.text

    # Authorization
    if not auth_manager.is_authorized(user_id, update.effective_user.username):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Input validation
    is_valid, error_msg = validate_text_input(text)
    if not is_valid:
        await update.message.reply_text(error_msg)
        logger.warning(f"Invalid input from user {user_id}: {error_msg}")
        return

    # Rate limiting
    allowed, rate_msg = rate_limiter.check_rate_limit(user_id)
    if not allowed:
        if rate_msg:
            await update.message.reply_text(rate_msg)
        return

    # Execute command
    await execute_claude_command(update, context, text)


async def handle_voice(update: Update, context):
    """Handle voice messages with validation."""
    user_id = update.effective_user.id
    voice = update.message.voice

    # Authorization
    if not auth_manager.is_authorized(user_id, update.effective_user.username):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Validate voice duration
    is_valid, error_msg = validate_voice_duration(voice.duration)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return

    # Rate limiting
    allowed, rate_msg = rate_limiter.check_rate_limit(user_id)
    if not allowed:
        if rate_msg:
            await update.message.reply_text(rate_msg)
        return

    # Process voice message
    # ... existing voice processing code ...
```

### 4. Network Security

#### 4.1 Firewall Configuration

Ensure UFW firewall is properly configured:

```bash
#!/bin/bash
# setup-firewall.sh

# Enable UFW
sudo ufw --force enable

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (critical - don't lock yourself out!)
sudo ufw allow 22/tcp comment 'SSH'

# Allow HTTP/HTTPS (for Coolify/web access)
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'

# Allow Coolify admin (optional - can use SSH tunnel instead)
# sudo ufw allow 8000/tcp comment 'Coolify Admin'

# Rate limit SSH to prevent brute force
sudo ufw limit 22/tcp

# Enable logging
sudo ufw logging on

# Show status
sudo ufw status verbose
```

#### 4.2 Fail2Ban for SSH Protection

Install and configure Fail2Ban:

```bash
# Install
sudo apt-get update
sudo apt-get install -y fail2ban

# Configure
sudo tee /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
backend = systemd
EOF

# Start service
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Check status
sudo fail2ban-client status sshd
```

#### 4.3 SSL/TLS Configuration

Coolify handles SSL automatically, but verify security headers:

```bash
# Test SSL configuration
curl -I https://claude.yourdomain.com

# Should include:
# Strict-Transport-Security: max-age=31536000
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
```

### 5. Docker Security

#### 5.1 Run Containers as Non-Root

Update Dockerfile:

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r botuser && useradd -r -g botuser botuser

# ... install dependencies ...

# Set ownership
RUN chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

CMD ["python", "bot.py"]
```

#### 5.2 Security Scanning

Add Trivy security scanning:

```bash
# Install Trivy
sudo apt-get install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install trivy

# Scan image for vulnerabilities
trivy image telegram-bot:latest

# Scan for critical/high only
trivy image --severity HIGH,CRITICAL telegram-bot:latest
```

### 6. Security Monitoring

#### 6.1 Security Event Logging

Create **bot/security_logger.py**:

```python
"""
Security event logging and monitoring.
"""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class SecurityEventLogger:
    """Log security-relevant events."""

    @staticmethod
    def log_unauthorized_access(user_id: int, username: Optional[str]):
        """Log unauthorized access attempt."""
        logger.warning(
            f"🚨 SECURITY: Unauthorized access attempt | "
            f"User ID: {user_id} | Username: @{username} | "
            f"Time: {datetime.now().isoformat()}"
        )

    @staticmethod
    def log_rate_limit_exceeded(user_id: int, username: Optional[str]):
        """Log rate limit violation."""
        logger.warning(
            f"⚠️  SECURITY: Rate limit exceeded | "
            f"User ID: {user_id} | Username: @{username} | "
            f"Time: {datetime.now().isoformat()}"
        )

    @staticmethod
    def log_invalid_input(user_id: int, reason: str):
        """Log invalid/malicious input."""
        logger.warning(
            f"🚨 SECURITY: Invalid input blocked | "
            f"User ID: {user_id} | Reason: {reason} | "
            f"Time: {datetime.now().isoformat()}"
        )

    @staticmethod
    def log_admin_action(admin_id: int, action: str, target: Optional[str] = None):
        """Log admin actions for audit trail."""
        logger.info(
            f"👤 ADMIN ACTION: {action} | "
            f"Admin ID: {admin_id} | Target: {target} | "
            f"Time: {datetime.now().isoformat()}"
        )

    @staticmethod
    def log_file_access(user_id: int, file_path: str, action: str):
        """Log file access for audit trail."""
        logger.info(
            f"📁 FILE ACCESS: {action} | "
            f"User ID: {user_id} | File: {file_path} | "
            f"Time: {datetime.now().isoformat()}"
        )


security_logger = SecurityEventLogger()
```

#### 6.2 Automated Security Alerts

Create **scripts/security-check.sh**:

```bash
#!/bin/bash
# security-check.sh - Check for security issues

echo "=== Security Health Check ==="
echo

# Check for failed login attempts
echo "1. Checking authentication logs..."
FAILED_LOGINS=$(docker logs telegram-bot 2>&1 | grep -c "Unauthorized access")
echo "   Failed login attempts: $FAILED_LOGINS"
if [ $FAILED_LOGINS -gt 10 ]; then
    echo "   ⚠️  WARNING: High number of failed logins!"
fi

# Check for rate limit violations
echo "2. Checking rate limit logs..."
RATE_LIMIT_HITS=$(docker logs telegram-bot 2>&1 | grep -c "Rate limit exceeded")
echo "   Rate limit violations: $RATE_LIMIT_HITS"

# Check for dangerous patterns detected
echo "3. Checking for blocked dangerous commands..."
DANGEROUS_BLOCKS=$(docker logs telegram-bot 2>&1 | grep -c "dangerous command detected")
echo "   Dangerous commands blocked: $DANGEROUS_BLOCKS"
if [ $DANGEROUS_BLOCKS -gt 0 ]; then
    echo "   🚨 ALERT: Dangerous commands were attempted!"
fi

# Check UFW status
echo "4. Checking firewall status..."
sudo ufw status | head -5

# Check fail2ban status
echo "5. Checking fail2ban..."
if command -v fail2ban-client &> /dev/null; then
    sudo fail2ban-client status sshd | grep "Currently banned"
else
    echo "   Fail2ban not installed"
fi

# Check for container running as root
echo "6. Checking container user..."
BOT_USER=$(docker exec telegram-bot whoami)
if [ "$BOT_USER" = "root" ]; then
    echo "   ⚠️  WARNING: Container running as root!"
else
    echo "   ✅ Container running as: $BOT_USER"
fi

# Check SSL certificate expiry
echo "7. Checking SSL certificate..."
DOMAIN="claude.yourdomain.com"
if command -v openssl &> /dev/null; then
    EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates | grep "notAfter")
    echo "   $EXPIRY"
else
    echo "   OpenSSL not available for checking"
fi

echo
echo "=== Security check complete ==="
```

Make executable:

```bash
chmod +x scripts/security-check.sh
```

---

## Security Checklist

### Pre-Production Security Audit

- [ ] **Access Control**
  - [ ] `ALLOWED_USER_IDS` is set (not empty)
  - [ ] `ADMIN_USER_IDS` is configured
  - [ ] User authentication is tested and working
  - [ ] Failed login attempts are logged
  - [ ] Users are auto-blocked after 5 failed attempts

- [ ] **API Keys**
  - [ ] All API keys are in environment variables (not hardcoded)
  - [ ] API keys are marked as "Secret" in Coolify
  - [ ] `.env` is in `.gitignore`
  - [ ] No API keys in git history
  - [ ] Production keys are different from development keys
  - [ ] API key rotation schedule is documented

- [ ] **Web UI**
  - [ ] Basic auth is enabled
  - [ ] Strong password is set (16+ characters)
  - [ ] Default credentials have been changed
  - [ ] HTTPS is enforced
  - [ ] SSL certificate is valid

- [ ] **Input Validation**
  - [ ] Text input length limits enforced
  - [ ] Voice duration limits enforced
  - [ ] Dangerous command patterns are blocked
  - [ ] Input validation is tested with malicious inputs

- [ ] **Network Security**
  - [ ] Firewall (UFW) is enabled
  - [ ] Only required ports are open (22, 80, 443)
  - [ ] SSH is rate-limited
  - [ ] Fail2ban is installed and running
  - [ ] SSL/TLS is properly configured

- [ ] **Docker Security**
  - [ ] Containers run as non-root user
  - [ ] Resource limits are set
  - [ ] Images have been scanned for vulnerabilities
  - [ ] No sensitive data in Docker images
  - [ ] Docker socket is mounted read-only where possible

- [ ] **Logging & Monitoring**
  - [ ] Security events are logged
  - [ ] Logs are sanitized (no API keys in logs)
  - [ ] Log rotation is configured
  - [ ] Security alerts are tested
  - [ ] Admin actions are audited

- [ ] **Backup Security**
  - [ ] Backups are encrypted
  - [ ] Backup access is restricted
  - [ ] Backup encryption keys are stored securely
  - [ ] Backup restore has been tested

- [ ] **Rate Limiting**
  - [ ] Rate limits are configured
  - [ ] Rate limit violations are logged
  - [ ] Rate limits are appropriate for usage

- [ ] **Documentation**
  - [ ] Security procedures are documented
  - [ ] Incident response plan exists
  - [ ] Emergency contacts are documented
  - [ ] Rollback procedures are documented

---

## Testing

### Security Test Plan

1. **Test Unauthorized Access**
   ```bash
   # Use different Telegram account (not in ALLOWED_USER_IDS)
   # Send /start command
   # Expected: "⛔ Unauthorized" message
   # Check logs: should show unauthorized access attempt
   ```

2. **Test Input Validation**
   ```bash
   # Send dangerous command: "rm -rf /"
   # Expected: Blocked with security warning
   # Send very long text (3000+ chars)
   # Expected: Rejected as too long
   ```

3. **Test Rate Limiting**
   ```bash
   # Send 15 messages rapidly
   # Expected: First 10 succeed, next 5 blocked
   ```

4. **Test Log Sanitization**
   ```bash
   docker logs telegram-bot | grep -i "sk-ant"
   # Expected: No API keys visible (should be ***REDACTED***)
   ```

5. **Test Firewall**
   ```bash
   sudo ufw status
   # Expected: Active, only ports 22/80/443 open
   ```

6. **Test SSL**
   ```bash
   curl -I https://claude.yourdomain.com
   # Expected: Security headers present
   # Expected: Valid SSL certificate
   ```

7. **Run Security Scan**
   ```bash
   trivy image telegram-bot:latest
   # Expected: No critical vulnerabilities
   ```

---

## Acceptance Criteria

- [ ] All items in security checklist are complete
- [ ] Unauthorized users cannot access bot
- [ ] Admin commands require admin privileges
- [ ] Dangerous inputs are blocked
- [ ] Rate limiting prevents abuse
- [ ] API keys are not visible in logs
- [ ] Firewall is active and configured correctly
- [ ] SSL certificate is valid
- [ ] Containers run as non-root
- [ ] No critical vulnerabilities in Docker images
- [ ] Security events are logged
- [ ] Security check script runs successfully

---

## Troubleshooting

### Issue: Legitimate users blocked

**Symptoms:**
- Authorized user gets "Unauthorized" message

**Solutions:**
```bash
# Verify user ID is in ALLOWED_USER_IDS
echo $ALLOWED_USER_IDS

# Get user's actual Telegram ID
# Ask them to message @userinfobot

# Add to Coolify environment variables
# Redeploy application
```

### Issue: Rate limiting too strict

**Symptoms:**
- Normal usage triggers rate limits

**Solutions:**
```python
# Adjust limits in rate_limiter.py
rate_limiter = RateLimiter(
    per_minute=20,  # Increase
    per_hour=120,
    per_day=600
)
```

### Issue: Firewall blocking legitimate traffic

**Symptoms:**
- Cannot access web UI
- Telegram webhook not working

**Solutions:**
```bash
# Check UFW logs
sudo tail -f /var/log/ufw.log

# Verify rules
sudo ufw status numbered

# Delete incorrect rule
sudo ufw delete <rule_number>

# Add correct rule
sudo ufw allow 443/tcp
```

---

## Rollback Procedure

If security hardening causes issues:

```bash
# 1. Disable authentication temporarily
# In Coolify, set:
ALLOWED_USER_IDS=  # Empty to allow all

# 2. Disable input validation
# Comment out validation checks in bot.py

# 3. Reload
docker compose restart telegram-bot

# 4. Debug the issue
docker logs telegram-bot -f

# 5. Re-enable security once fixed
```

---

## Related Documentation

- [Design Document - Section 7: Security](/Users/vlad/WebstormProjects/claude-remote-runner/docs/design.md#7-security-considerations)
- [Implementation Plan - Phase 6](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation_plan.md#phase-6-monitoring-backup--optimization-2-3-hours)
- [Step 23: Performance Optimization](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_23_performance_optimization.md)
- [Step 25: User Documentation](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_25_user_documentation.md)

---

**Status:** Complete
**Last Updated:** February 4, 2026
**Next Step:** [Step 25: User Documentation](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_25_user_documentation.md)
