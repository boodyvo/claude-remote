# Step 3: Local Docker Compose Testing

**Estimated Time:** 1-2 hours
**Prerequisites:**
- Steps 1-2 completed (project setup, credentials obtained)
- Docker Desktop installed and running
- .env file with valid API keys
- 8GB+ RAM available
- 10GB+ disk space available

**Deliverable:** Working Docker Compose stack running locally with claudebox-web accessible at localhost:3000

## Overview

This step creates and tests the Docker infrastructure locally before deploying to Coolify. We'll build a docker-compose.yml file that defines all services (web UI, bot, volumes), test that Claude Code works inside containers, and verify volume persistence.

Testing locally first provides several advantages:
- Faster iteration (no deployment wait times)
- Easier debugging (direct access to logs)
- Cost-free testing (no cloud resources consumed)
- Confidence before production deployment

By the end of this step, you'll have a fully functional local development environment that mirrors the production setup.

## Implementation Details

### What to Build

1. **docker-compose.yml:** Define all services and their configurations
2. **requirements.txt:** Python dependencies for the bot
3. **claudebox-web service:** Web-based terminal for Claude Code
4. **telegram-bot service:** Placeholder service (full implementation in later steps)
5. **Docker volumes:** Persistent storage for workspace and Claude config
6. **Health checks:** Monitor service status
7. **Network:** Internal Docker network for service communication

### How to Implement

#### Step 3.1: Create requirements.txt for Bot Service

```bash
# Create bot/requirements.txt
cat > bot/requirements.txt << 'EOF'
# Telegram Bot Framework
python-telegram-bot==21.9

# OpenAI API for Whisper transcription
openai==1.59.5

# Anthropic API for Claude Code (if needed for direct API calls)
anthropic==0.41.0

# Environment variable management
python-dotenv==1.0.0

# HTTP requests
requests==2.31.0
EOF
```

#### Step 3.2: Create docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Web-based terminal for browser access to Claude Code
  claudebox-web:
    image: koogle/claudebox:latest
    container_name: claudebox-web
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY is required}
      - BASIC_AUTH_USER=${BASIC_AUTH_USER:-}
      - BASIC_AUTH_PASS=${BASIC_AUTH_PASS:-}
      - PORT=3000
      - NODE_ENV=development
    volumes:
      - workspace:/workspace
      - claude-config:/root/.claude
    ports:
      - "3000:3000"
    restart: unless-stopped
    networks:
      - claude-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Telegram bot for voice control (minimal implementation for now)
  telegram-bot:
    image: python:3.11-slim
    container_name: telegram-bot
    working_dir: /app
    volumes:
      - ./bot:/app                    # Bot source code
      - ./sessions:/app/sessions      # Bot session persistence
      - workspace:/workspace          # Access to project files
      - claude-config:/root/.claude   # Access to Claude config for session management
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN:?TELEGRAM_TOKEN is required}
      - DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY:?DEEPGRAM_API_KEY is required}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY is required}
      - WEBHOOK_URL=${WEBHOOK_URL:-}
      - ALLOWED_USER_IDS=${ALLOWED_USER_IDS:-}
      - BOT_MODE=polling
    command: >
      bash -c "
        apt-get update &&
        apt-get install -y ffmpeg curl git &&
        pip install --no-cache-dir -r requirements.txt &&
        echo 'Bot container ready. Waiting for implementation...' &&
        tail -f /dev/null
      "
    restart: unless-stopped
    networks:
      - claude-network
    depends_on:
      claudebox-web:
        condition: service_healthy

volumes:
  # Project files and user code
  workspace:
    driver: local

  # Claude Code configuration and session history
  claude-config:
    driver: local

networks:
  # Internal network for service communication
  claude-network:
    driver: bridge
EOF
```

**Key Configuration Notes:**

- **`${VAR:?message}`**: Marks variables as required; Docker Compose will fail if missing
- **`${VAR:-default}`**: Uses default value if variable not set
- **`restart: unless-stopped`**: Containers auto-restart on failure or system reboot
- **`depends_on` with `condition: service_healthy`**: Bot waits for web service to be fully ready
- **Health checks**: Allow Docker to monitor service status
- **Named volumes**: Persist data across container restarts

#### Step 3.3: Create Placeholder Bot Script

For now, we'll create a minimal bot.py that just keeps the container running:

```bash
cat > bot/bot.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal bot placeholder for Step 3.
Full implementation will be added in Steps 4-7.
"""

import os
import time
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Placeholder main function."""
    logger.info("Bot container is running")
    logger.info(f"TELEGRAM_TOKEN: {'Set' if os.getenv('TELEGRAM_TOKEN') else 'Not set'}")
    logger.info(f"DEEPGRAM_API_KEY: {'Set' if os.getenv('DEEPGRAM_API_KEY') else 'Not set'}")
    logger.info(f"ANTHROPIC_API_KEY: {'Set' if os.getenv('ANTHROPIC_API_KEY') else 'Not set'}")
    logger.info("Waiting for full implementation in Steps 4-7...")

    # Keep container running
    while True:
        time.sleep(60)

if __name__ == '__main__':
    main()
EOF

chmod +x bot/bot.py
```

#### Step 3.4: Validate docker-compose.yml

```bash
# Check syntax
docker-compose config

# Expected: Parsed YAML output with all services
# If errors, check for indentation issues or syntax errors
```

#### Step 3.5: Start Services

```bash
# Pull images (may take 5-10 minutes)
docker-compose pull

# Start all services in detached mode
docker-compose up -d

# Watch logs
docker-compose logs -f
```

**Expected Log Output:**

```
claudebox-web  | Server listening on port 3000
claudebox-web  | Claude Code ready
telegram-bot   | Bot container ready. Waiting for implementation...
```

#### Step 3.6: Verify Services Are Running

```bash
# Check container status
docker-compose ps

# Expected output:
# NAME                 STATUS              PORTS
# claudebox-web        Up 1 minute         0.0.0.0:3000->3000/tcp
# telegram-bot         Up 1 minute
```

```bash
# Check health status
docker ps --format "table {{.Names}}\t{{.Status}}"

# Expected:
# NAMES              STATUS
# claudebox-web      Up 2 minutes (healthy)
# telegram-bot       Up 2 minutes
```

#### Step 3.7: Test Web UI Access

1. **Open browser:**
   ```
   http://localhost:3000
   ```

2. **Expected:** Terminal interface loads (xterm.js)

3. **Test Claude Code:**
   ```bash
   # In the web terminal, type:
   claude --version

   # Expected: Claude Code version number
   ```

4. **Test basic command:**
   ```bash
   claude -p "Create a hello.py file that prints 'Hello from Docker'"
   ```

5. **Expected:** Claude creates the file, you can see it in the terminal

#### Step 3.8: Test Volume Persistence

**Test workspace volume:**

```bash
# Create test file via web UI
# In web terminal:
echo "test content" > /workspace/test.txt
cat /workspace/test.txt

# Now restart containers
docker-compose restart

# Open web UI again and check file still exists
cat /workspace/test.txt
# Expected: File persists with same content
```

**Test Claude config volume:**

```bash
# Check Claude config directory exists
docker exec claudebox-web ls -la /root/.claude

# Run a Claude command to create session
docker exec claudebox-web claude -p "Hello Claude" --output-format json

# Check session was saved
docker exec claudebox-web ls -la /root/.claude/projects/
# Expected: Session files present
```

#### Step 3.9: Test Bot Container

```bash
# Check bot logs
docker logs telegram-bot

# Expected:
# Bot container is running
# TELEGRAM_TOKEN: Set
# DEEPGRAM_API_KEY: Set
# ANTHROPIC_API_KEY: Set
# Waiting for full implementation in Steps 4-7...

# Verify ffmpeg is installed (needed for voice conversion)
docker exec telegram-bot ffmpeg -version

# Verify Python packages installed
docker exec telegram-bot pip list | grep -E "telegram|openai|anthropic"
# Expected: All three packages listed
```

#### Step 3.10: Test Network Communication

```bash
# Test that bot can reach web service
docker exec telegram-bot curl -f http://claudebox-web:3000

# Expected: HTML content from web UI (or HTTP 200 OK)

# Test DNS resolution within network
docker exec telegram-bot ping -c 3 claudebox-web

# Expected: Successful pings
```

### Code Examples

**Test Script for Complete Validation:**

```bash
cat > validate_docker.sh << 'EOF'
#!/bin/bash
# Validate Docker Compose setup

echo "=" "Validating Docker Compose Setup" "="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# Check docker-compose file exists
if [ ! -f docker-compose.yml ]; then
    echo -e "${RED}✗ docker-compose.yml not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose.yml exists${NC}"

# Check .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓ .env file exists${NC}"

# Validate docker-compose syntax
if ! docker-compose config > /dev/null 2>&1; then
    echo -e "${RED}✗ docker-compose.yml has syntax errors${NC}"
    exit 1
fi
echo -e "${GREEN}✓ docker-compose.yml syntax valid${NC}"

# Check services are running
if ! docker-compose ps | grep -q "Up"; then
    echo -e "${RED}✗ Services are not running${NC}"
    echo "Start with: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✓ Services are running${NC}"

# Check claudebox-web is healthy
if docker inspect claudebox-web --format='{{.State.Health.Status}}' | grep -q "healthy"; then
    echo -e "${GREEN}✓ claudebox-web is healthy${NC}"
else
    echo -e "${RED}✗ claudebox-web is not healthy${NC}"
    docker logs claudebox-web --tail 20
    exit 1
fi

# Check web UI is accessible
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Web UI is accessible at http://localhost:3000${NC}"
else
    echo -e "${RED}✗ Web UI is not accessible${NC}"
    exit 1
fi

# Check Claude Code is installed in claudebox
if docker exec claudebox-web which claude > /dev/null 2>&1; then
    version=$(docker exec claudebox-web claude --version 2>&1)
    echo -e "${GREEN}✓ Claude Code installed: $version${NC}"
else
    echo -e "${RED}✗ Claude Code not found in container${NC}"
    exit 1
fi

# Check bot dependencies installed
if docker exec telegram-bot pip list | grep -q "python-telegram-bot"; then
    echo -e "${GREEN}✓ Bot dependencies installed${NC}"
else
    echo -e "${RED}✗ Bot dependencies not installed${NC}"
    exit 1
fi

# Check ffmpeg installed in bot
if docker exec telegram-bot which ffmpeg > /dev/null 2>&1; then
    echo -e "${GREEN}✓ ffmpeg installed in bot container${NC}"
else
    echo -e "${RED}✗ ffmpeg not installed${NC}"
    exit 1
fi

# Check volumes exist
for volume in workspace claude-config; do
    if docker volume ls | grep -q "claude-remote-runner_$volume"; then
        echo -e "${GREEN}✓ Volume exists: $volume${NC}"
    else
        echo -e "${RED}✗ Volume missing: $volume${NC}"
        exit 1
    fi
done

# Check network communication
if docker exec telegram-bot curl -f http://claudebox-web:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Network communication working (bot → web)${NC}"
else
    echo -e "${RED}✗ Network communication failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ All Docker Compose tests passed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Access web UI: http://localhost:3000"
echo "2. Test Claude command in terminal"
echo "3. Proceed to Step 4: Telegram Bot Foundation"
EOF

chmod +x validate_docker.sh
```

Run validation:
```bash
./validate_docker.sh
```

### Project Structure

After this step, your structure should be:

```
claude-remote-runner/
├── docker-compose.yml          # ← NEW: Service definitions
├── validate_docker.sh          # ← NEW: Validation script
├── .env                        # API keys (git-ignored)
├── .env.example
├── README.md
├── LICENSE
├── .gitignore
├── bot/
│   ├── bot.py                  # ← NEW: Placeholder bot
│   └── requirements.txt        # ← NEW: Python dependencies
├── workspace/                  # Docker volume (empty)
├── sessions/                   # Docker volume (empty)
├── backups/
└── docs/
```

**Docker Artifacts Created:**
```bash
# View Docker resources
docker-compose ps                  # Running containers
docker volume ls                   # Created volumes
docker network ls | grep claude    # Created network
```

## Testing & Validation

### Test Cases

**Test 1: Docker Compose Syntax Valid**
```bash
docker-compose config
# Expected: No errors, YAML output displayed
```

**Test 2: Images Pulled Successfully**
```bash
docker images | grep -E "koogle/claudebox|python"
# Expected: Both images present with latest tags
```

**Test 3: Services Start Successfully**
```bash
docker-compose up -d
sleep 30  # Wait for startup
docker-compose ps
# Expected: All services showing "Up" status
```

**Test 4: Web UI Accessible**
```bash
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK
```

**Test 5: Claude Code Works in Container**
```bash
docker exec claudebox-web claude --version
# Expected: Version number (e.g., "1.x.x")

docker exec claudebox-web claude -p "Print current date" --output-format json
# Expected: JSON response with Claude's output
```

**Test 6: Bot Container Has Required Tools**
```bash
docker exec telegram-bot python --version
# Expected: Python 3.11.x

docker exec telegram-bot ffmpeg -version
# Expected: ffmpeg version info

docker exec telegram-bot git --version
# Expected: git version info
```

**Test 7: Volumes Persist Data**
```bash
# Create test file
docker exec claudebox-web sh -c "echo 'test' > /workspace/persist.txt"

# Restart container
docker-compose restart claudebox-web
sleep 10

# Check file still exists
docker exec claudebox-web cat /workspace/persist.txt
# Expected: "test"
```

**Test 8: Network Communication Works**
```bash
docker exec telegram-bot ping -c 2 claudebox-web
# Expected: 2 packets transmitted, 2 received, 0% packet loss
```

**Test 9: Environment Variables Loaded**
```bash
docker exec telegram-bot env | grep -E "TELEGRAM|OPENAI|ANTHROPIC"
# Expected: All three API keys shown (partially masked)
```

**Test 10: Health Checks Working**
```bash
docker inspect claudebox-web --format='{{.State.Health.Status}}'
# Expected: "healthy"
```

### Acceptance Criteria

- [ ] docker-compose.yml created with all required services
- [ ] bot/requirements.txt created with all dependencies
- [ ] bot/bot.py placeholder created
- [ ] `docker-compose config` validates without errors
- [ ] Both images pulled successfully (koogle/claudebox, python:3.11-slim)
- [ ] Both services start and reach "Up" status
- [ ] claudebox-web health check passes (status: healthy)
- [ ] Web UI accessible at http://localhost:3000
- [ ] Terminal loads in browser
- [ ] Claude Code command executes successfully in web terminal
- [ ] Bot container installs all dependencies (ffmpeg, git, Python packages)
- [ ] Both Docker volumes created (workspace, claude-config)
- [ ] Files persist in volumes after container restart
- [ ] Network communication works between services
- [ ] Environment variables loaded correctly in both containers
- [ ] Logs show no critical errors
- [ ] validate_docker.sh script passes all checks

### How to Test

**Complete Test Procedure:**

```bash
# 1. Start fresh
docker-compose down -v  # Remove containers and volumes
docker-compose up -d

# 2. Wait for services to be healthy
sleep 45

# 3. Run validation script
./validate_docker.sh

# 4. Manual verification
# Open browser: http://localhost:3000
# In web terminal, run:
#   claude -p "List files in /workspace"
#   echo "manual test" > /workspace/manual.txt
#   cat /workspace/manual.txt

# 5. Check logs for errors
docker-compose logs

# 6. Test restart persistence
docker-compose restart
sleep 20
docker exec claudebox-web cat /workspace/manual.txt
# Should output: "manual test"

# 7. Final status check
docker-compose ps
docker stats --no-stream
```

## Troubleshooting

### Issue 1: Port 3000 Already in Use

**Symptoms:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:3000: bind: address already in use
```

**Solutions:**

**Option 1: Stop conflicting service**
```bash
# Find what's using port 3000
lsof -i :3000
# Or on Linux:
netstat -tulpn | grep 3000

# Kill the process
kill <PID>
```

**Option 2: Use different port**
```yaml
# In docker-compose.yml, change ports:
ports:
  - "3001:3000"  # Host:Container

# Then access: http://localhost:3001
```

### Issue 2: Docker Daemon Not Running

**Symptoms:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solutions:**

**macOS:**
```bash
# Start Docker Desktop app
open -a Docker

# Wait for it to start (check menu bar icon)
```

**Linux:**
```bash
# Start Docker service
sudo systemctl start docker

# Enable auto-start
sudo systemctl enable docker
```

### Issue 3: Environment Variables Not Loaded

**Symptoms:**
```
ERROR: The ANTHROPIC_API_KEY variable is not set
```

**Solutions:**

1. **Check .env file exists:**
   ```bash
   ls -la .env
   ```

2. **Check .env syntax:**
   ```bash
   # Should have no spaces around =
   cat .env | grep "ANTHROPIC"
   # Good: ANTHROPIC_API_KEY=sk-ant-...
   # Bad:  ANTHROPIC_API_KEY = sk-ant-...
   ```

3. **Restart with explicit env file:**
   ```bash
   docker-compose --env-file .env up -d
   ```

4. **Verify variables in container:**
   ```bash
   docker-compose config | grep ANTHROPIC
   ```

### Issue 4: claudebox-web Container Fails Health Check

**Symptoms:**
```
claudebox-web unhealthy
```

**Solutions:**

1. **Check logs:**
   ```bash
   docker logs claudebox-web --tail 50
   ```

2. **Check if service is actually running:**
   ```bash
   docker exec claudebox-web curl localhost:3000
   ```

3. **Increase health check timeout:**
   ```yaml
   healthcheck:
     start_period: 60s  # Increase from 40s
     timeout: 20s       # Increase from 10s
   ```

4. **Test manually:**
   ```bash
   curl -v http://localhost:3000
   ```

### Issue 5: Bot Container Keeps Restarting

**Symptoms:**
```bash
docker-compose ps
# Shows: Restarting (1) 5 seconds ago
```

**Solutions:**

1. **Check logs:**
   ```bash
   docker logs telegram-bot --tail 50
   ```

2. **Common issues:**
   - Syntax error in bot.py
   - Missing dependency in requirements.txt
   - Failed apt-get install (network issue)

3. **Test dependencies manually:**
   ```bash
   docker-compose run --rm telegram-bot bash
   # Inside container:
   pip install -r requirements.txt
   python bot.py
   ```

### Issue 6: Volume Data Not Persisting

**Symptoms:**
```
Files created in /workspace disappear after restart
```

**Solutions:**

1. **Check volume mounts:**
   ```bash
   docker inspect claudebox-web | grep -A 10 Mounts
   ```

2. **Verify volume exists:**
   ```bash
   docker volume ls | grep workspace
   ```

3. **Check volume data:**
   ```bash
   docker volume inspect claude-remote-runner_workspace
   # Note the Mountpoint location
   ```

4. **Recreate volumes if corrupted:**
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

### Issue 7: Out of Disk Space

**Symptoms:**
```
Error response from daemon: no space left on device
```

**Solutions:**

1. **Check disk usage:**
   ```bash
   docker system df
   ```

2. **Clean up:**
   ```bash
   # Remove unused images, containers, networks
   docker system prune -a

   # Remove unused volumes (CAREFUL: deletes data)
   docker volume prune
   ```

3. **Free space on host:**
   ```bash
   # macOS: Increase Docker Desktop disk limit
   # Settings → Resources → Disk image size

   # Linux: Free system disk space
   df -h
   ```

### Issue 8: Can't Access Web UI from Browser

**Symptoms:**
```
Browser shows "This site can't be reached" or timeout
```

**Solutions:**

1. **Check service is running:**
   ```bash
   docker-compose ps claudebox-web
   # Should show "Up"
   ```

2. **Check port binding:**
   ```bash
   docker port claudebox-web
   # Expected: 3000/tcp -> 0.0.0.0:3000
   ```

3. **Test with curl first:**
   ```bash
   curl http://localhost:3000
   # If works: browser/firewall issue
   # If fails: container issue
   ```

4. **Check firewall:**
   ```bash
   # macOS: System Preferences → Security → Firewall
   # Linux: sudo ufw status
   ```

5. **Try different browser or incognito mode**

## Rollback Procedure

### Stop and Remove All Containers

```bash
# Stop services
docker-compose down

# Remove containers and networks (keeps volumes)
docker-compose down --remove-orphans

# Remove containers, networks, AND volumes (DELETES DATA)
docker-compose down -v

# Verify cleanup
docker-compose ps
docker volume ls | grep claude
```

### Reset to Clean State

```bash
# Complete cleanup
docker-compose down -v
docker system prune -f

# Remove project-specific images
docker rmi koogle/claudebox:latest
docker rmi python:3.11-slim

# Verify clean state
docker ps -a
docker images
docker volume ls
```

### Restore Previous docker-compose.yml

```bash
# If you have Git history
git checkout HEAD~1 docker-compose.yml

# Or restore from backup
cp docker-compose.yml.backup docker-compose.yml

# Restart with old version
docker-compose up -d
```

### Remove Docker Artifacts

```bash
# Remove specific volume
docker volume rm claude-remote-runner_workspace

# Remove specific network
docker network rm claude-remote-runner_claude-network

# Remove specific container
docker rm -f claudebox-web telegram-bot
```

## Next Step

Once all acceptance criteria are met and validation passes, proceed to:

**Step 4: Telegram Bot Foundation**
- File: `docs/implementation/step_04_bot_foundation.md`
- Duration: 1 hour
- Goal: Create minimal working Telegram bot that responds to /start command

Before proceeding, ensure:
1. Docker Compose services running successfully
2. Web UI accessible at localhost:3000
3. Claude Code works in web terminal
4. Bot container has all dependencies installed
5. Volumes persist data across restarts
6. validate_docker.sh passes all checks
7. No critical errors in logs

**Checkpoint:** You now have a working local Docker environment that mirrors the production setup. The infrastructure is ready, and we can now implement the bot logic in the following steps.

**Save Your Work:**
```bash
git add docker-compose.yml bot/requirements.txt bot/bot.py validate_docker.sh
git commit -m "Add Docker Compose configuration

- Add docker-compose.yml with claudebox-web and telegram-bot services
- Add bot/requirements.txt with all Python dependencies
- Add placeholder bot/bot.py
- Add validate_docker.sh test script
- Configure named volumes for persistence
- Set up health checks and networking
- Test local deployment successfully"
```
