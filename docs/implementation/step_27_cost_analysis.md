# Step 27: Cost Analysis & Optimization Guide

**Estimated Time:** 30 minutes
**Phase:** 7 - Documentation & Handoff
**Prerequisites:** Operational runbooks complete (Step 26)

---

## Overview

This step provides comprehensive cost analysis, tracking mechanisms, and optimization strategies for the claude-remote-runner system. It helps understand actual vs. projected costs, identify optimization opportunities, and maintain budget control.

### Context

Understanding and controlling costs is critical for:
- Staying within budget
- Identifying cost spikes early
- Optimizing resource utilization
- Making informed scaling decisions
- Justifying infrastructure spending

### Goals

- Calculate accurate monthly costs
- Set up cost tracking and monitoring
- Identify optimization opportunities
- Create cost forecasting models
- Document scaling cost implications
- Establish cost alerts and thresholds

---

## Implementation Details

### 1. Cost Breakdown

#### Monthly Cost Components

| Component | Provider | Base Cost | Variable Cost | Total Est. |
|-----------|----------|-----------|---------------|------------|
| **Infrastructure** |
| VPS (CPX21) | Hetzner | €9.00 ($9.90) | - | $9.90 |
| Bandwidth | Hetzner | Included | $0 (20TB free) | $0.00 |
| Storage Box (optional) | Hetzner | €3.20 ($3.50) | - | $0.00 |
| Domain | Registrar | $1.00 | - | $1.00 |
| **APIs** |
| Claude API | Anthropic | - | $0.015/1K input + $0.075/1K output tokens | $20-50 |
| Deepgram API | OpenAI | - | $0.0043/minute | $18-36 |
| **Total** | | **$10.90** | **$38-86** | **$48.90-96.90** |

#### Detailed Cost Calculations

**1. Infrastructure Costs (Fixed)**

```
Hetzner CPX21:          €9.00/month  = $9.90/month
Domain (annual ÷ 12):   $12/year     = $1.00/month
SSL Certificate:        $0 (Let's Encrypt free)
───────────────────────────────────────────────
Infrastructure Total:                  $10.90/month
```

**2. Claude API Costs (Variable)**

Assumptions:
- 10 requests per day
- Average 2,000 input tokens per request
- Average 1,000 output tokens per response

```
Daily usage:
  Input:  10 × 2,000 = 20,000 tokens
  Output: 10 × 1,000 = 10,000 tokens

Monthly usage (30 days):
  Input:  600,000 tokens = 600K
  Output: 300,000 tokens = 300K

Monthly cost:
  Input:  600K × $0.015/1K = $9.00
  Output: 300K × $0.075/1K = $22.50

  Total: $31.50/month (light usage)
```

High usage scenario (30 requests/day):
```
Monthly usage:
  Input:  1.8M tokens
  Output: 900K tokens

Cost: $27 + $67.50 = $94.50/month (heavy usage)
```

**3. Deepgram API Costs (Variable)**

Assumptions:
- 50% of requests use voice (5 per day)
- Average voice message: 15 seconds

```
Daily voice minutes: 5 × 15s = 75 seconds = 1.25 minutes
Monthly voice minutes: 37.5 minutes

Cost: 37.5 × $0.0043 = $0.23/month (light usage)
```

Alternative with GPT-4o Audio Transcription (cheaper):
```
Cost: 37.5 × $0.003 = $0.11/month
Savings: 50%
```

High usage scenario (20 voice messages/day, 30 seconds each):
```
Monthly voice minutes: 300 minutes
Cost: 300 × $0.0043 = $1.80/month
```

#### Cost Summary by Usage Level

| Usage Level | Requests/Day | Voice/Day | Infrastructure | Claude API | Deepgram API | **Total** |
|-------------|--------------|-----------|----------------|------------|-------------|-----------|
| **Minimal** | 5 | 2 | $10.90 | $15.75 | $0.12 | **$26.77** |
| **Light** | 10 | 5 | $10.90 | $31.50 | $0.23 | **$42.63** |
| **Moderate** | 20 | 10 | $10.90 | $63.00 | $0.45 | **$74.35** |
| **Heavy** | 30 | 15 | $10.90 | $94.50 | $0.68 | **$106.08** |

### 2. Cost Tracking Setup

#### 2.1 Create Cost Tracking Spreadsheet

**Template: cost-tracking.xlsx**

**Sheet 1: Monthly Tracking**

| Month | Infrastructure | Claude API | Deepgram API | Other | Total | Budget | Delta |
|-------|----------------|------------|-------------|-------|-------|--------|-------|
| Jan 2026 | $10.90 | $32.45 | $0.25 | $0 | $43.60 | $75.00 | -$31.40 |
| Feb 2026 | $10.90 | $48.20 | $0.38 | $0 | $59.48 | $75.00 | -$15.52 |
| ... | | | | | | | |

**Sheet 2: Daily Usage Log**

| Date | Requests | Voice Messages | Voice Minutes | Est. Claude Cost | Est. Whisper Cost |
|------|----------|----------------|---------------|------------------|-------------------|
| 2026-02-01 | 12 | 5 | 1.2 | $1.13 | $0.007 |
| 2026-02-02 | 8 | 3 | 0.8 | $0.75 | $0.005 |
| ... | | | | | |

**Sheet 3: Forecasting**

```
Current monthly rate: $X
Projected next month: $Y
Annual projection: $Z
Variance from budget: ±%
```

#### 2.2 API Usage Monitoring Script

Create **scripts/track-costs.sh**:

```bash
#!/bin/bash
# track-costs.sh - Track API usage and estimate costs

set -e

# Configuration
LOG_FILE="cost-tracking-$(date +%Y-%m).log"
BOT_LOG="docker logs telegram-bot --since 24h"

echo "=== Cost Tracking for $(date +%Y-%m-%d) ===" | tee -a $LOG_FILE
echo

# Count requests today
REQUESTS_TODAY=$($BOT_LOG 2>&1 | grep -c "execute_claude_command" || echo 0)
echo "Total requests today: $REQUESTS_TODAY" | tee -a $LOG_FILE

# Count voice messages today
VOICE_TODAY=$($BOT_LOG 2>&1 | grep -c "Voice message from user" || echo 0)
echo "Voice messages today: $VOICE_TODAY" | tee -a $LOG_FILE

# Estimate voice minutes (assume 15 sec average)
VOICE_MINUTES=$(echo "scale=2; $VOICE_TODAY * 15 / 60" | bc)
echo "Estimated voice minutes: $VOICE_MINUTES" | tee -a $LOG_FILE

# Estimate costs
# Claude: assume 2K input, 1K output tokens per request
CLAUDE_DAILY=$(echo "scale=2; $REQUESTS_TODAY * ((2000 * 0.015 / 1000) + (1000 * 0.075 / 1000))" | bc)
echo "Estimated Claude cost today: \$$CLAUDE_DAILY" | tee -a $LOG_FILE

# Whisper: $0.0043 per minute
WHISPER_DAILY=$(echo "scale=4; $VOICE_MINUTES * 0.006" | bc)
echo "Estimated Whisper cost today: \$$WHISPER_DAILY" | tee -a $LOG_FILE

# Total daily
TOTAL_DAILY=$(echo "scale=2; $CLAUDE_DAILY + $WHISPER_DAILY" | bc)
echo "Total API cost today: \$$TOTAL_DAILY" | tee -a $LOG_FILE

# Project monthly
MONTHLY_PROJECTION=$(echo "scale=2; $TOTAL_DAILY * 30" | bc)
echo "Projected monthly API cost: \$$MONTHLY_PROJECTION" | tee -a $LOG_FILE

echo
echo "=== Month-to-Date ===" | tee -a $LOG_FILE

# Sum current month
MONTH_START="$(date +%Y-%m)-01"
REQUESTS_MTD=$(docker logs telegram-bot --since ${MONTH_START}T00:00:00 2>&1 | grep -c "execute_claude_command" || echo 0)
VOICE_MTD=$(docker logs telegram-bot --since ${MONTH_START}T00:00:00 2>&1 | grep -c "Voice message from user" || echo 0)

echo "Total requests this month: $REQUESTS_MTD" | tee -a $LOG_FILE
echo "Total voice messages this month: $VOICE_MTD" | tee -a $LOG_FILE

# Check budget alert (example: $75/month budget for APIs)
API_BUDGET=75
if (( $(echo "$MONTHLY_PROJECTION > $API_BUDGET" | bc -l) )); then
    echo "⚠️  WARNING: Projected cost (\$$MONTHLY_PROJECTION) exceeds budget (\$$API_BUDGET)" | tee -a $LOG_FILE
else
    echo "✅ Projected cost within budget" | tee -a $LOG_FILE
fi

echo
echo "=== Anthropic Console ===" | tee -a $LOG_FILE
echo "Check actual usage: https://console.anthropic.com/" | tee -a $LOG_FILE
echo
echo "=== OpenAI Dashboard ===" | tee -a $LOG_FILE
echo "Check actual usage: https://platform.openai.com/usage" | tee -a $LOG_FILE

echo
echo "Log saved to: $LOG_FILE"
```

Make executable:

```bash
chmod +x scripts/track-costs.sh
```

Run daily:

```bash
./scripts/track-costs.sh
```

#### 2.3 Cost Alert Setup

Add to crontab for daily cost checks:

```bash
# Edit crontab
crontab -e

# Add daily cost check at 11 PM
0 23 * * * /path/to/claude-remote-runner/scripts/track-costs.sh

# Add weekly summary every Sunday at 9 AM
0 9 * * 0 /path/to/claude-remote-runner/scripts/weekly-cost-report.sh
```

**scripts/weekly-cost-report.sh:**

```bash
#!/bin/bash
# weekly-cost-report.sh - Weekly cost summary

echo "=== Weekly Cost Report - Week of $(date +%Y-%m-%d) ==="
echo

# Aggregate last 7 days
WEEK_START=$(date -d '7 days ago' +%Y-%m-%dT00:00:00)
REQUESTS_WEEK=$(docker logs telegram-bot --since $WEEK_START 2>&1 | grep -c "execute_claude_command" || echo 0)
VOICE_WEEK=$(docker logs telegram-bot --since $WEEK_START 2>&1 | grep -c "Voice message from user" || echo 0)

echo "Total requests this week: $REQUESTS_WEEK"
echo "Total voice messages this week: $VOICE_WEEK"
echo "Average requests per day: $(echo "scale=1; $REQUESTS_WEEK / 7" | bc)"
echo

# Estimated costs
CLAUDE_WEEK=$(echo "scale=2; $REQUESTS_WEEK * 0.105" | bc)
VOICE_MINUTES=$(echo "scale=2; $VOICE_WEEK * 15 / 60" | bc)
WHISPER_WEEK=$(echo "scale=2; $VOICE_MINUTES * 0.006" | bc)
TOTAL_WEEK=$(echo "scale=2; $CLAUDE_WEEK + $WHISPER_WEEK" | bc)

echo "Estimated costs this week:"
echo "  Claude API: \$$CLAUDE_WEEK"
echo "  Deepgram API: \$$WHISPER_WEEK"
echo "  Total: \$$TOTAL_WEEK"
echo

# Monthly projection
MONTHLY_PROJ=$(echo "scale=2; $TOTAL_WEEK * 4.33" | bc)
echo "Projected monthly API cost: \$$MONTHLY_PROJ"

# Compare to budget
BUDGET=75
PERCENT=$(echo "scale=1; ($MONTHLY_PROJ / $BUDGET) * 100" | bc)
echo "Budget usage: $PERCENT%"

if (( $(echo "$MONTHLY_PROJ > $BUDGET" | bc -l) )); then
    echo "⚠️  ALERT: Projected to exceed budget!"
fi

# Email report (optional)
# mail -s "Weekly Cost Report" admin@yourdomain.com < /tmp/weekly-report.txt
```

### 3. Cost Optimization Strategies

#### 3.1 Claude API Optimization

**Strategy 1: Use /compact regularly**

```python
# In bot code
async def execute_claude_command(update: Update, context, prompt: str):
    # ... existing code ...

    # Auto-compact every 15 turns (reduced from 20)
    turn_count = context.user_data.get('turn_count', 0) + 1
    context.user_data['turn_count'] = turn_count

    if turn_count >= 15:
        logger.info("Auto-compacting session to reduce token usage")
        subprocess.run(
            ['claude', '-p', '/compact', '--resume', session_id],
            cwd=str(WORKSPACE_DIR)
        )
        context.user_data['turn_count'] = 0
```

**Savings:** 20-30% reduction in token usage

**Strategy 2: Shorter context windows**

```python
claude_cmd = [
    'claude',
    '-p', prompt,
    '--max-turns', '5',  # Reduced from 10
    '--output-format', 'stream-json'
]
```

**Savings:** 15-25% reduction in token usage

**Strategy 3: Use Claude 3 Haiku for simple queries**

```python
def should_use_haiku(prompt: str) -> bool:
    """Determine if we can use cheaper Haiku model."""
    simple_keywords = ['show', 'list', 'what is', 'explain']
    return any(keyword in prompt.lower() for keyword in simple_keywords)

# In execute_claude_command:
if should_use_haiku(prompt):
    claude_cmd.extend(['--model', 'claude-3-haiku-20240307'])
```

**Savings:** 95% cost reduction for simple queries
- Sonnet: $0.015/1K input, $0.075/1K output
- Haiku: $0.00025/1K input, $0.00125/1K output

#### 3.2 Deepgram API Optimization

**Strategy 1: Use GPT-4o Audio Transcription**

```python
# Switch from whisper-1 to gpt-4o-audio-preview
transcript = openai.Audio.transcribe(
    model="gpt-4o-audio-preview",  # 50% cheaper
    file=audio_file
)
```

**Savings:** 50% reduction ($0.0043 → $0.003 per minute)

**Strategy 2: Limit voice message length**

```python
# In validators.py
MAX_VOICE_DURATION = 60  # Reduced from 120 seconds

def validate_voice_duration(duration: int) -> Tuple[bool, str]:
    if duration > MAX_VOICE_DURATION:
        return False, (
            f"⚠️ Voice message too long (max {MAX_VOICE_DURATION} seconds).\n"
            f"Tip: Break into multiple shorter messages or use text."
        )
    return True, ""
```

**Savings:** Encourages shorter, more focused messages

**Strategy 3: Cache transcriptions**

```python
# Already implemented in Step 23
# Avoid re-transcribing identical audio
audio_hash = hash_audio_file(wav_file)
cached = transcription_cache.get(audio_hash)
if cached:
    return cached
```

**Savings:** Eliminate duplicate transcriptions

#### 3.3 Infrastructure Optimization

**Strategy 1: Right-size VPS**

Current: CPX21 (3 vCPU, 8GB RAM) = €9/month

If under-utilized:
- Downgrade to CPX11 (2 vCPU, 4GB RAM) = €5/month
- **Savings:** €4/month ($4.40)

If over-utilized:
- Monitor with `docker stats`
- Only upgrade if consistently >80% CPU or RAM

**Strategy 2: Optimize Docker images**

Already implemented in Step 23:
- Multi-stage builds
- Smaller base images
- .dockerignore

**Benefit:** Faster deployments, less bandwidth

**Strategy 3: Compress backups**

```yaml
# In docker-compose.yml backup service
environment:
  BACKUP_COMPRESSION_LEVEL: "9"  # Maximum compression
```

**Savings:** Reduce storage and bandwidth usage

### 4. Cost Forecasting Model

#### 4.1 Usage-Based Projection

**Formula:**

```
Monthly Cost = Infrastructure_Fixed + (Daily_Requests × Days × Cost_Per_Request)

Where:
  Infrastructure_Fixed = $10.90
  Cost_Per_Request = $0.105 (avg Claude) + $0.0043 (avg Whisper if voice)

Example:
  10 requests/day × 30 days × $0.105 = $31.50 (Claude)
  5 voice/day × 30 days × 0.25 min × $0.0043 = $0.23 (Whisper)
  Total = $10.90 + $31.50 + $0.23 = $42.63/month
```

#### 4.2 Growth Scenarios

| Scenario | Requests/Day | Monthly Cost | Annual Cost |
|----------|--------------|--------------|-------------|
| **Personal Use** | 5-10 | $26-43 | $312-516 |
| **Small Team (3)** | 15-30 | $53-106 | $636-1,272 |
| **Team (10)** | 50-100 | $176-352 | $2,112-4,224 |
| **Heavy Team (10)** | 100-200 | $352-703 | $4,224-8,436 |

**Scaling Cost Analysis:**

When to upgrade infrastructure:
- **>50 requests/day:** Consider CPX31 (+€4/month)
- **>150 requests/day:** Consider CPX41 (+€16/month)
- **>300 requests/day:** Consider multiple instances + load balancer

### 5. Budget Management

#### 5.1 Set Spending Limits

**Anthropic Console:**
1. Visit https://console.anthropic.com/settings/limits
2. Set monthly spending limit (e.g., $100)
3. Enable email alerts at 50%, 80%, 100%

**OpenAI Dashboard:**
1. Visit https://platform.openai.com/account/billing/limits
2. Set hard limit (e.g., $50/month)
3. Enable email notifications

#### 5.2 Implement Bot-Level Rate Limits

Already implemented in Step 23:
```python
rate_limiter = RateLimiter(
    per_minute=10,
    per_hour=60,
    per_day=300  # Limits total daily costs
)
```

**Adjust based on budget:**

```python
# For tighter budget control
rate_limiter = RateLimiter(
    per_minute=5,   # Slower pace
    per_hour=30,    # Half the requests
    per_day=150     # Halves monthly API costs
)
```

#### 5.3 Cost-Aware Features

**Add cost info to /usage command:**

```python
async def handle_usage_stats(update: Update, context):
    """Show usage stats with cost estimates."""
    user_id = update.effective_user.id
    stats = rate_limiter.get_usage_stats(user_id)

    # Calculate estimated costs
    requests_today = stats['day']['used']
    claude_cost = requests_today * 0.105

    message = f"📊 Your Usage Today:\n\n"
    message += f"**Requests:** {requests_today}\n"
    message += f"**Est. Cost:** ${claude_cost:.2f}\n\n"
    message += f"**Limits:**\n"
    message += f"Per hour: {stats['hour']['used']}/{stats['hour']['limit']}\n"
    message += f"Per day: {stats['day']['used']}/{stats['day']['limit']}\n"

    await update.message.reply_text(message, parse_mode='Markdown')
```

### 6. Cost Monitoring Dashboard

Create **scripts/cost-dashboard.sh**:

```bash
#!/bin/bash
# cost-dashboard.sh - Real-time cost dashboard

watch -n 60 '
clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Claude Remote Runner - Cost Dashboard             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "=== Today ($(date +%Y-%m-%d)) ==="
REQUESTS=$(docker logs telegram-bot --since $(date +%Y-%m-%d)T00:00:00 2>&1 | grep -c "execute_claude_command" || echo 0)
VOICE=$(docker logs telegram-bot --since $(date +%Y-%m-%d)T00:00:00 2>&1 | grep -c "Voice message" || echo 0)
echo "Requests: $REQUESTS"
echo "Voice messages: $VOICE"
echo "Est. Claude cost: \$$(echo "scale=2; $REQUESTS * 0.105" | bc)"
echo "Est. Whisper cost: \$$(echo "scale=4; $VOICE * 0.25 * 0.006" | bc)"
echo
echo "=== This Month ==="
MONTH_START="$(date +%Y-%m)-01"
REQUESTS_MTD=$(docker logs telegram-bot --since ${MONTH_START}T00:00:00 2>&1 | grep -c "execute_claude_command" || echo 0)
echo "Total requests: $REQUESTS_MTD"
echo "Est. Claude cost: \$$(echo "scale=2; $REQUESTS_MTD * 0.105" | bc)"
BUDGET=75
echo "Budget: \$$BUDGET"
echo
echo "Press Ctrl+C to exit"
'
```

---

## Acceptance Criteria

- [ ] Complete cost breakdown documented
- [ ] Monthly cost tracking spreadsheet created
- [ ] Cost tracking scripts implemented and tested
- [ ] Cost optimization strategies documented
- [ ] Spending limits set in API consoles
- [ ] Cost alerts configured
- [ ] Forecasting model created
- [ ] Budget management procedures documented
- [ ] Cost dashboard script created
- [ ] Actual costs match projections ±15%

---

## Testing

### Cost Tracking Test

1. **Run cost tracking script:**
   ```bash
   ./scripts/track-costs.sh
   ```
   - Expected: Shows daily usage and projections

2. **Generate test usage:**
   - Send 10 test commands
   - Run tracking script again
   - Verify counts increased

3. **Check API consoles:**
   - Anthropic: Verify usage appears
   - OpenAI: Verify usage appears
   - Compare with script estimates

---

## Related Documentation

- [Implementation Plan - Phase 7](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation_plan.md#phase-7-documentation--handoff-1-2-hours)
- [Step 23: Performance Optimization](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_23_performance_optimization.md)
- [Step 26: Operational Runbooks](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_26_operational_runbooks.md)

---

**Status:** Complete
**Last Updated:** February 4, 2026
**Next Step:** [Step 28: Final Testing & Acceptance](/Users/vlad/WebstormProjects/claude-remote-runner/docs/implementation/step_28_final_testing.md)
