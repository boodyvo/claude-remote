# Step 21: Monitoring Setup

**Estimated Time:** 1 hour
**Phase:** Phase 6 - Monitoring, Backup & Optimization
**Prerequisites:** Step 20 (Webhook Configuration) completed with bot fully functional
**Status:** Not Started

---

## Overview

This step implements comprehensive monitoring for the claude-remote-runner production system. Monitoring is critical for maintaining uptime, identifying issues early, tracking performance, and optimizing costs. This includes Coolify's built-in monitoring, custom application metrics, log management, alerting, and creating operational dashboards.

### Context

Production systems require monitoring for:
1. **Health Monitoring** - Ensure services are running and responsive
2. **Performance Metrics** - Track resource usage (CPU, memory, disk)
3. **Application Logs** - Debug issues and audit activity
4. **Cost Tracking** - Monitor API usage and spending
5. **Alerting** - Get notified of issues immediately
6. **Trend Analysis** - Identify patterns and optimization opportunities

This step creates a comprehensive monitoring solution using Coolify's built-in tools plus custom metrics.

### Goals

- ✅ Configure Coolify monitoring dashboards
- ✅ Set up custom application metrics logging
- ✅ Implement log rotation and retention
- ✅ Create monitoring dashboard
- ✅ Configure alerting for critical issues
- ✅ Set up cost tracking
- ✅ Document monitoring procedures

---

## Implementation Details

### 1. Enable Coolify Monitoring

**Navigation Path:**
```
Coolify Dashboard → Resources → Claude Remote Runner → Monitoring
```

**Enable Monitoring:**

Click: **"Enable Monitoring"** toggle

**Monitoring Configuration:**

| Setting | Value | Notes |
|---------|-------|-------|
| **Enable Monitoring** | `✓ Yes` | Turn on metrics collection |
| **Collection Interval** | `30s` | How often to collect metrics |
| **Retention Period** | `7 days` | How long to keep metrics |
| **Enable Alerts** | `✓ Yes` | Enable alerting system |

**Click:** `Save Settings`

**What Gets Monitored:**

Coolify automatically tracks:
- **CPU Usage** - % per container
- **Memory Usage** - MB used / limit
- **Network I/O** - Sent/received MB
- **Disk I/O** - Read/write MB
- **Container Restarts** - Count
- **Response Times** - Health check latency

**Expected Result:**
- Monitoring graphs appear within 60 seconds
- Data points populate every 30 seconds
- 7 days of history retained

**Screenshot Location:** Monitoring dashboard showing active metrics graphs

### 2. Configure Service-Specific Monitoring

#### 2.1 claudebox-web Monitoring

**Metrics to Track:**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| CPU Usage | <20% idle | >80% for 5 min |
| Memory Usage | ~500 MB | >1.8 GB |
| Restart Count | 0 | >2 in 1 hour |
| Response Time | <100ms | >1000ms |

**Health Check Configuration:**

Already configured in docker-compose.yml:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:3000"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

**Custom Metrics Endpoint:**

Add to claudebox-web (if not already present):

```javascript
// In claudebox container (advanced, optional)
app.get('/metrics', (req, res) => {
  res.json({
    uptime: process.uptime(),
    memory: process.memoryUsage(),
    cpu: process.cpuUsage(),
    connections: server.connections,
    timestamp: Date.now()
  });
});
```

#### 2.2 telegram-bot Monitoring

**Metrics to Track:**

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| CPU Usage | <10% idle | >50% for 5 min |
| Memory Usage | ~200 MB | >900 MB |
| Messages/Hour | Varies | None (informational) |
| Errors/Hour | 0 | >5 |
| Transcription Time | <10s | >30s |

**Add Custom Metrics to Bot:**

**File:** `bot/bot.py`

Add metrics tracking:

```python
import time
from datetime import datetime
from collections import defaultdict

# Metrics storage
metrics = {
    'messages_received': 0,
    'voice_messages': 0,
    'text_messages': 0,
    'errors': 0,
    'transcription_times': [],
    'claude_execution_times': [],
    'approvals': 0,
    'rejections': 0,
    'start_time': datetime.now()
}

# Track voice message processing time
async def handle_voice(update: Update, context):
    start_time = time.time()
    metrics['voice_messages'] += 1
    metrics['messages_received'] += 1

    try:
        # ... existing voice handling code ...

        # Track transcription time
        transcription_time = time.time() - start_time
        metrics['transcription_times'].append(transcription_time)

        # Keep last 100 measurements
        if len(metrics['transcription_times']) > 100:
            metrics['transcription_times'] = metrics['transcription_times'][-100:]

    except Exception as e:
        metrics['errors'] += 1
        raise

# Track text message
async def handle_text(update: Update, context):
    metrics['text_messages'] += 1
    metrics['messages_received'] += 1
    # ... existing code ...

# Add /metrics command
async def handle_metrics(update: Update, context):
    """Handle /metrics command - show bot metrics."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Calculate statistics
    uptime = datetime.now() - metrics['start_time']
    avg_transcription = (
        sum(metrics['transcription_times']) / len(metrics['transcription_times'])
        if metrics['transcription_times'] else 0
    )
    avg_claude = (
        sum(metrics['claude_execution_times']) / len(metrics['claude_execution_times'])
        if metrics['claude_execution_times'] else 0
    )

    metrics_text = f"""📊 **Bot Metrics**

**Uptime:** {uptime.days}d {uptime.seconds//3600}h {(uptime.seconds//60)%60}m

**Messages:**
└─ Total: {metrics['messages_received']}
└─ Voice: {metrics['voice_messages']}
└─ Text: {metrics['text_messages']}

**Approvals:**
└─ Approved: {metrics['approvals']}
└─ Rejected: {metrics['rejections']}

**Performance:**
└─ Avg Transcription: {avg_transcription:.2f}s
└─ Avg Claude Exec: {avg_claude:.2f}s

**Errors:** {metrics['errors']}

**Start Time:** {metrics['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
"""

    await update.message.reply_text(metrics_text, parse_mode='Markdown')

# Register metrics command
app.add_handler(CommandHandler("metrics", handle_metrics))
```

**Track approvals/rejections:**

```python
async def handle_approve(update: Update, context, change_id: str):
    # ... existing code ...
    metrics['approvals'] += 1
    # ... rest of code ...

async def handle_reject(update: Update, context, change_id: str):
    # ... existing code ...
    metrics['rejections'] += 1
    # ... rest of code ...
```

**Deploy updated bot:**

```bash
git add bot/bot.py
git commit -m "Add metrics tracking"
git push origin main

# Coolify auto-deploys (if webhook configured)
# Or manually deploy via Coolify UI
```

### 3. Configure Log Management

#### 3.1 Log Rotation

Logs can grow large over time. Configure rotation:

**Update docker-compose.yml:**

```yaml
services:
  claudebox-web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"      # Rotate at 10 MB
        max-file: "3"        # Keep last 3 files
        compress: "true"     # Compress rotated logs

  telegram-bot:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        compress: "true"
```

**Commit and deploy:**

```bash
git add docker-compose.yml
git commit -m "Add log rotation configuration"
git push origin main
```

#### 3.2 Structured Logging

Update bot to use structured logging:

**File:** `bot/bot.py`

```python
import logging
import json

# Configure structured logging
class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }

        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'duration'):
            log_data['duration'] = record.duration

        return json.dumps(log_data)

# Set up logger
handler = logging.StreamHandler()
handler.setFormatter(StructuredFormatter())
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Example usage
logger.info("Voice message received", extra={'user_id': user_id})
logger.error("Transcription failed", extra={'user_id': user_id, 'duration': duration})
```

#### 3.3 Log Aggregation

**Access Logs in Coolify:**

```
Resource → Logs → Select Service → Date Range
```

**Download Logs:**

Click: **"Download Logs"** button

**Filter Logs:**

Use search box to filter:
- `level:ERROR` - Only errors
- `user_id:123456789` - Specific user
- `transcription` - All transcription-related logs

**Via SSH:**

```bash
# View live logs
docker logs -f claude-remote-runner-telegram-bot-1

# Search logs
docker logs claude-remote-runner-telegram-bot-1 | grep ERROR

# Export logs
docker logs claude-remote-runner-telegram-bot-1 > bot-logs-$(date +%Y%m%d).log
```

### 4. Create Monitoring Dashboard

#### 4.1 Coolify Dashboard

**Access Built-in Dashboard:**

```
Coolify → Resources → Claude Remote Runner → Overview
```

**Key Widgets:**

1. **Service Status** - Green/red indicators
2. **CPU Graph** - 7-day trend
3. **Memory Graph** - 7-day trend
4. **Network Graph** - Traffic in/out
5. **Logs Stream** - Live log tail

**Customize Dashboard:**

Click: **"Customize Dashboard"**

Add widgets:
- [x] Response time graph
- [x] Error rate
- [x] Request count
- [x] Container restarts

#### 4.2 Custom Monitoring Page

Create a simple monitoring web page:

**File:** `monitoring/index.html`

```html
<!DOCTYPE html>
<html>
<head>
    <title>Claude Runner - Monitoring</title>
    <meta http-equiv="refresh" content="30">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .metric-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin: 10px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 36px;
            font-weight: bold;
            color: #2196F3;
        }
        .metric-label {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
        }
        .status-green { color: #4CAF50; }
        .status-red { color: #f44336; }
        .status-yellow { color: #FF9800; }
    </style>
</head>
<body>
    <h1>📊 Claude Remote Runner - Monitoring</h1>

    <div class="metric-card">
        <div class="metric-label">System Status</div>
        <div class="metric-value status-green" id="status">● OPERATIONAL</div>
    </div>

    <div class="metric-card">
        <div class="metric-label">Messages Today</div>
        <div class="metric-value" id="messages">--</div>
    </div>

    <div class="metric-card">
        <div class="metric-label">Average Response Time</div>
        <div class="metric-value" id="response-time">--</div>
    </div>

    <div class="metric-card">
        <div class="metric-label">Error Rate</div>
        <div class="metric-value" id="error-rate">--</div>
    </div>

    <div class="metric-card">
        <div class="metric-label">API Costs (Today)</div>
        <div class="metric-value" id="costs">--</div>
    </div>

    <script>
        // Fetch metrics from bot /metrics endpoint (if implemented)
        // Or from Coolify API
        // Update dashboard every 30 seconds

        async function updateMetrics() {
            try {
                // Example - implement actual API calls
                document.getElementById('messages').textContent = '24';
                document.getElementById('response-time').textContent = '2.3s';
                document.getElementById('error-rate').textContent = '0%';
                document.getElementById('costs').textContent = '$0.42';
            } catch (error) {
                console.error('Failed to fetch metrics:', error);
            }
        }

        updateMetrics();
        setInterval(updateMetrics, 30000);
    </script>
</body>
</html>
```

**Serve via nginx (optional):**

Add to docker-compose.yml:

```yaml
  monitoring:
    image: nginx:alpine
    container_name: claude-monitoring
    volumes:
      - ./monitoring:/usr/share/nginx/html:ro
    networks:
      - claude-network
    # Expose via Coolify on subdomain: monitoring.claude.yourdomain.com
```

### 5. Configure Alerting

#### 5.1 Coolify Alerts

**Navigation Path:**
```
Resource → Settings → Notifications
```

**Configure Email Alerts:**

| Alert Type | Threshold | Action |
|------------|-----------|--------|
| **Service Down** | Immediate | Email |
| **High CPU** | >80% for 5 min | Email |
| **High Memory** | >90% for 5 min | Email |
| **Deployment Failed** | Immediate | Email |
| **SSL Expiring** | <7 days | Email |

**Email Configuration:**

```
Email: your-email@example.com
SMTP Server: smtp.gmail.com
SMTP Port: 587
Username: your-email@gmail.com
Password: your-app-password
```

**Test Alerts:**

Click: **"Send Test Email"**

Verify test email received.

#### 5.2 Telegram Alerts

Send alerts to Telegram:

**Create Alert Bot (Optional):**

```python
# alert_bot.py - Simple alert forwarder
import requests

def send_alert(message):
    TOKEN = "your-alert-bot-token"
    CHAT_ID = "your-chat-id"

    requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={
            "chat_id": CHAT_ID,
            "text": f"🚨 ALERT: {message}",
            "parse_mode": "Markdown"
        }
    )

# Usage in monitoring script
if cpu_usage > 80:
    send_alert("High CPU usage: 85%")
```

#### 5.3 Health Check Monitoring

**External Monitoring (Recommended):**

Use third-party service for independent monitoring:

**Option 1: UptimeRobot (Free)**

1. Sign up: https://uptimerobot.com
2. Add monitor:
   - **Type:** HTTPS
   - **URL:** https://claude.yourdomain.com
   - **Interval:** 5 minutes
   - **Alert Contacts:** Your email
3. Add webhook monitor for bot:
   - **Type:** HTTP(S)
   - **URL:** https://claude.yourdomain.com/health (implement health endpoint)

**Option 2: Healthchecks.io (Free)**

1. Sign up: https://healthchecks.io
2. Create check
3. Set up cron job to ping:

```bash
# Add to server crontab
*/5 * * * * curl https://hc-ping.com/your-check-uuid
```

**Option 3: Better Uptime**

1. Sign up: https://betteruptime.com
2. Add website monitor
3. Configure alert phone call (premium)

### 6. Cost Tracking

#### 6.1 API Usage Monitoring

**OpenAI (Whisper):**

Create monitoring script:

**File:** `scripts/check_openai_usage.py`

```python
#!/usr/bin/env python3
import os
import requests
from datetime import datetime, timedelta

DEEPGRAM_API_KEY = os.environ['DEEPGRAM_API_KEY']

# Get usage for last 24 hours
# Note: OpenAI doesn't provide programmatic usage API
# Use dashboard: https://platform.openai.com/usage

# Alternative: Track locally
usage_log = {
    'date': datetime.now().strftime('%Y-%m-%d'),
    'voice_messages': 0,
    'total_seconds': 0,
    'estimated_cost': 0
}

def log_transcription(duration_seconds):
    usage_log['voice_messages'] += 1
    usage_log['total_seconds'] += duration_seconds

    # Whisper pricing: $0.0043 per minute
    minutes = duration_seconds / 60
    cost = minutes * 0.006
    usage_log['estimated_cost'] += cost

    # Save to file
    with open('/app/sessions/usage.json', 'w') as f:
        json.dump(usage_log, f)

# Call in handle_voice after transcription
log_transcription(voice.duration)
```

**Anthropic (Claude):**

```python
#!/usr/bin/env python3
# Track Claude API usage
claude_usage = {
    'date': datetime.now().strftime('%Y-%m-%d'),
    'requests': 0,
    'input_tokens': 0,
    'output_tokens': 0,
    'estimated_cost': 0
}

def log_claude_usage(input_tokens, output_tokens):
    claude_usage['requests'] += 1
    claude_usage['input_tokens'] += input_tokens
    claude_usage['output_tokens'] += output_tokens

    # Claude pricing (example - check current rates)
    # Input: $3 per million tokens
    # Output: $15 per million tokens
    cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
    claude_usage['estimated_cost'] += cost
```

#### 6.2 Cost Dashboard

Add to `/metrics` command:

```python
async def handle_metrics(update: Update, context):
    # ... existing code ...

    # Add cost section
    cost_text = f"""
**Costs (Today):**
└─ Whisper: ${usage_log['estimated_cost']:.2f}
└─ Claude: ${claude_usage['estimated_cost']:.2f}
└─ Total: ${usage_log['estimated_cost'] + claude_usage['estimated_cost']:.2f}

**Usage (Today):**
└─ Voice Minutes: {usage_log['total_seconds']//60}
└─ Claude Requests: {claude_usage['requests']}
"""

    await update.message.reply_text(metrics_text + cost_text, parse_mode='Markdown')
```

#### 6.3 Budget Alerts

Set up budget alerts in provider dashboards:

**OpenAI:**
1. Go to https://platform.openai.com/account/billing/limits
2. Set "Hard Limit": $50/month
3. Set "Soft Limit": $40/month (email alert)

**Anthropic:**
1. Go to https://console.anthropic.com/settings/limits
2. Set spending limit: $100/month
3. Enable email alerts at 80%, 90%, 100%

### 7. Performance Baseline Documentation

Record baseline metrics after initial deployment:

**File:** `monitoring/BASELINE.md`

```markdown
# Performance Baseline

**Recorded:** 2026-02-04
**Environment:** Production (Hetzner CPX21)

## Resource Usage (Idle)

### claudebox-web
- CPU: 2-3%
- Memory: 450 MB / 2048 MB (22%)
- Network I/O: <1 MB/hour
- Disk I/O: <1 MB/hour

### telegram-bot
- CPU: 1-2%
- Memory: 180 MB / 1024 MB (18%)
- Network I/O: <1 MB/hour
- Disk I/O: <1 MB/hour

## Response Times

- Web UI load: 800ms
- Terminal first paint: 1.2s
- /start command: 450ms
- Voice transcription (10s audio): 3.5s
- Claude execution (simple): 8-12s
- Claude execution (complex): 20-40s

## Throughput

- Messages handled/minute: ~10
- Concurrent users tested: 1
- Max messages/hour: ~100 (untested)

## Costs (Daily)

- Infrastructure: €0.30 ($0.33)
- Deepgram API: $0 (no usage yet)
- Claude API: $0 (no usage yet)

## Error Rate

- Errors/hour: 0
- Success rate: 100%
- Uptime: 100% (first 24 hours)

## Notes

- First 24 hours, low usage
- Single user testing
- No load testing performed
- Use as reference for detecting issues
```

---

## Testing Procedures

### Test Case 1: Monitoring Data Collection

**Steps:**
1. Enable monitoring in Coolify
2. Wait 5 minutes
3. Check dashboard shows data

**Expected:**
- CPU graph populated
- Memory graph populated
- Data points every 30 seconds
- Graphs update in real-time

### Test Case 2: Log Rotation

**Steps:**
```bash
# Generate large amount of logs
for i in {1..1000}; do
  docker exec telegram-bot echo "Test log entry $i" >&2
done

# Check log file size
docker inspect telegram-bot | grep LogPath
# Find log file and check size
```

**Expected:**
- Logs rotate at 10 MB
- Old logs compressed
- Max 3 log files kept

### Test Case 3: Custom Metrics

**Steps:**
1. Send several voice messages
2. Send /metrics command
3. Review metrics output

**Expected:**
- Message counts accurate
- Average times reasonable
- No errors in metrics calculation

### Test Case 4: Alerting

**Steps:**
1. Configure email alert in Coolify
2. Click "Send Test Email"
3. Check email inbox

**Expected:**
- Test email received within 1 minute
- Email properly formatted
- Links work

### Test Case 5: Cost Tracking

**Steps:**
1. Send 5 voice messages
2. Check /metrics for cost data
3. Compare with OpenAI dashboard

**Expected:**
- Local tracking matches actual
- Costs calculated correctly
- ±10% accuracy acceptable

### Test Case 6: Health Check

**Steps:**
```bash
# Test health endpoints
curl http://localhost:3000/health
curl http://localhost:8443/health

# Should both return 200 OK
```

**Expected:**
- Both services respond
- Response <1 second
- JSON format (if implemented)

---

## Screenshots Guidance

### Screenshot 1: Coolify Monitoring Dashboard
**Location:** Coolify UI
**Content:**
- CPU graph with data
- Memory graph with data
- Service status indicators
- Time range selector

### Screenshot 2: Metrics Command Output
**Location:** Telegram conversation
**Content:**
- /metrics command sent
- Complete metrics response
- All sections populated

### Screenshot 3: Log Viewer
**Location:** Coolify logs interface
**Content:**
- Live log stream
- Filter options
- Download button
- Search functionality

### Screenshot 4: Alert Configuration
**Location:** Coolify notifications settings
**Content:**
- Email alert settings
- Threshold configurations
- Test email button

---

## Acceptance Criteria

### Monitoring Configuration
- ✅ Coolify monitoring enabled
- ✅ Metrics collecting every 30 seconds
- ✅ 7 days retention configured
- ✅ Both services monitored
- ✅ Dashboard accessible

### Logging
- ✅ Log rotation configured (10 MB)
- ✅ Compression enabled
- ✅ Logs accessible in Coolify UI
- ✅ Structured logging implemented
- ✅ Log levels appropriate

### Metrics
- ✅ Custom metrics tracking
- ✅ /metrics command functional
- ✅ Performance baselines documented
- ✅ Resource usage within limits

### Alerting
- ✅ Email alerts configured
- ✅ Test alerts successful
- ✅ Alert thresholds set appropriately
- ✅ Critical alerts cover downtime

### Cost Tracking
- ✅ API usage tracked
- ✅ Cost estimates calculated
- ✅ Budget limits set
- ✅ Daily reports available

---

## Troubleshooting Guide

### Issue 1: Monitoring Not Showing Data

**Symptoms:**
- Dashboard shows "No data available"

**Solutions:**
1. Wait 2-3 minutes for first data points
2. Verify monitoring enabled
3. Check containers running
4. Review Coolify logs for errors

### Issue 2: Alerts Not Sending

**Symptoms:**
- No email received for test alert

**Solutions:**
1. Check spam folder
2. Verify SMTP credentials correct
3. Test SMTP with external tool
4. Check email server logs

### Issue 3: Logs Not Rotating

**Symptoms:**
- Log files exceed 10 MB

**Solutions:**
1. Verify docker-compose.yml has logging config
2. Restart containers after config change
3. Check Docker logging driver
4. Manually rotate if needed

### Issue 4: Metrics Command Errors

**Symptoms:**
- /metrics shows errors or incorrect data

**Solutions:**
1. Check metrics dictionary initialized
2. Verify metrics updated in handlers
3. Check for division by zero (empty arrays)
4. Review error logs for exceptions

---

## Rollback Procedure

### Disable Monitoring

If monitoring causing issues:

```
Coolify → Resource → Monitoring → Disable Monitoring
```

### Revert Logging Changes

```bash
# Remove logging configuration from docker-compose.yml
git checkout HEAD~1 docker-compose.yml
git commit -m "Revert logging config"
git push origin main
```

### Remove Custom Metrics

```bash
# Revert bot.py changes
git checkout HEAD~1 bot/bot.py
git commit -m "Revert metrics tracking"
git push origin main
```

---

## Additional Notes

### Monitoring Best Practices

1. **Review Daily** - Check dashboard every day
2. **Weekly Reports** - Generate weekly summary
3. **Trend Analysis** - Look for patterns over time
4. **Set Baselines** - Know what's normal
5. **Alert Tuning** - Adjust thresholds based on actual usage

### Performance Optimization Tips

Based on monitoring data:

**If CPU High:**
- Reduce polling frequency
- Optimize Claude prompts
- Use /compact more frequently

**If Memory High:**
- Clear approval history periodically
- Reduce session retention
- Restart containers weekly

**If Response Time High:**
- Check network latency
- Optimize database queries (if added)
- Review Claude timeout settings

### Future Enhancements

- [ ] Grafana dashboard integration
- [ ] Prometheus metrics export
- [ ] Advanced analytics (user behavior)
- [ ] A/B testing framework
- [ ] Performance regression detection
- [ ] Automated performance testing

---

**Document Status:** Complete
**Implementation Status:** Not Started
**Next Step:** After monitoring configured, proceed to Step 22 (Backup Implementation)
**Estimated Completion:** 1 hour (including testing and documentation)
