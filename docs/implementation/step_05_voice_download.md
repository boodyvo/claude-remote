# Step 5: Voice Message Download & Conversion

**Estimated Time:** 1 hour
**Prerequisites:**
- Steps 1-4 completed (bot foundation working)
- ffmpeg installed in bot container
- Telegram bot receiving messages
- sessions/ directory writable

**Deliverable:** Bot can download voice messages from Telegram and convert OGG to WAV format using ffmpeg

## Overview

This step implements the first part of voice processing: downloading voice messages from Telegram and converting them to a format suitable for transcription. Telegram sends voice messages in OGG Opus format, but most speech-to-text APIs (including Deepgram) work better with WAV format at specific sample rates.

We'll implement:
- Voice message file download via Telegram API
- OGG to WAV conversion using ffmpeg
- Proper file cleanup to prevent disk space issues
- Error handling for network and conversion failures

This sets the foundation for Step 6 (Whisper transcription).

## Implementation Details

### What to Build

1. **Voice Handler:** Async function to handle voice messages
2. **File Download:** Download voice.ogg from Telegram
3. **Format Conversion:** Convert OGG Opus to WAV (16kHz, mono)
4. **File Management:** Unique filenames, cleanup after use
5. **Error Handling:** Network errors, conversion failures
6. **Logging:** Track download and conversion progress

### How to Implement

#### Step 5.1: Update bot/bot.py - Voice Handler Implementation

Replace the placeholder `handle_voice` function with this complete implementation:

```python
async def handle_voice(update: Update, context) -> None:
    """
    Handle voice messages from users.

    Downloads voice message from Telegram, converts to WAV format.
    In Step 6, this will add Whisper transcription.
    """
    user_id = update.effective_user.id

    # Check authorization
    if not check_authorization(user_id):
        logger.warning(f"Unauthorized voice message from user {user_id}")
        await update.message.reply_text("⛔ Unauthorized")
        return

    logger.info(f"Voice message received from user {user_id}")

    # Send "processing" message
    status_msg = await update.message.reply_text(
        "🎤 **Voice message received**\n\n"
        "⏳ Downloading...",
        parse_mode='Markdown'
    )

    try:
        # Step 1: Download voice file from Telegram
        voice_file_id = update.message.voice.file_id
        duration = update.message.voice.duration  # Duration in seconds

        logger.info(f"Voice file ID: {voice_file_id}, duration: {duration}s")

        # Create unique filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ogg_path = f'{config.SESSIONS_DIR}/voice_{user_id}_{timestamp}.ogg'
        wav_path = f'{config.SESSIONS_DIR}/voice_{user_id}_{timestamp}.wav'

        # Download file
        voice_file = await context.bot.get_file(voice_file_id)
        await voice_file.download_to_drive(ogg_path)

        file_size = os.path.getsize(ogg_path)
        logger.info(f"Downloaded voice file: {ogg_path} ({file_size} bytes)")

        # Update status
        await status_msg.edit_text(
            "🎤 **Voice message received**\n\n"
            f"✓ Downloaded ({duration}s)\n"
            "⏳ Converting format...",
            parse_mode='Markdown'
        )

        # Step 2: Convert OGG to WAV using ffmpeg
        conversion_result = subprocess.run(
            [
                'ffmpeg',
                '-y',                    # Overwrite output file if exists
                '-i', ogg_path,         # Input file
                '-ar', '16000',         # Sample rate: 16kHz (optimal for Whisper)
                '-ac', '1',             # Audio channels: 1 (mono)
                '-acodec', 'pcm_s16le', # Codec: 16-bit PCM
                wav_path                # Output file
            ],
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout
        )

        if conversion_result.returncode != 0:
            logger.error(f"ffmpeg conversion failed: {conversion_result.stderr}")
            await status_msg.edit_text(
                "❌ **Conversion failed**\n\n"
                "Failed to convert audio format.\n"
                "Please try recording again.",
                parse_mode='Markdown'
            )
            return

        wav_size = os.path.getsize(wav_path)
        logger.info(f"Converted to WAV: {wav_path} ({wav_size} bytes)")

        # Step 3: Success - ready for transcription
        await status_msg.edit_text(
            "🎤 **Voice message processed**\n\n"
            f"✓ Downloaded ({duration}s, {file_size} bytes)\n"
            f"✓ Converted to WAV ({wav_size} bytes)\n\n"
            "⏳ Transcription coming in Step 6...\n\n"
            f"Files saved:\n"
            f"• {os.path.basename(ogg_path)}\n"
            f"• {os.path.basename(wav_path)}",
            parse_mode='Markdown'
        )

        # Store paths in context for cleanup later
        context.user_data['last_voice_files'] = {
            'ogg': ogg_path,
            'wav': wav_path
        }

        logger.info(f"Voice processing complete for user {user_id}")

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg conversion timeout")
        await status_msg.edit_text(
            "❌ **Conversion timeout**\n\n"
            "Audio conversion took too long.\n"
            "Try a shorter voice message.",
            parse_mode='Markdown'
        )
        # Cleanup
        if os.path.exists(ogg_path):
            os.remove(ogg_path)

    except Exception as e:
        logger.error(f"Voice processing error: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ **Processing failed**\n\n"
            f"An error occurred: {str(e)[:100]}\n\n"
            "Please try again.",
            parse_mode='Markdown'
        )
        # Cleanup
        if os.path.exists(ogg_path):
            os.remove(ogg_path)
        if os.path.exists(wav_path):
            os.remove(wav_path)
```

#### Step 5.2: Add subprocess Import

At the top of bot/bot.py, add:

```python
import subprocess
```

So the imports section looks like:

```python
import os
import sys
import logging
import subprocess  # ← Add this
from pathlib import Path
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    PicklePersistence,
    filters
)
```

#### Step 5.3: Add Cleanup Command (Optional but Recommended)

Add a new command to manually clean up old voice files:

```python
async def handle_cleanup(update: Update, context) -> None:
    """Clean up old voice files to save disk space."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    logger.info(f"Cleanup requested by user {user_id}")

    try:
        # Find all voice files older than 1 hour
        import glob
        import time

        voice_files = glob.glob(f'{config.SESSIONS_DIR}/voice_*.ogg') + \
                      glob.glob(f'{config.SESSIONS_DIR}/voice_*.wav')

        current_time = time.time()
        old_files = []

        for file_path in voice_files:
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > 3600:  # 1 hour = 3600 seconds
                old_files.append(file_path)

        if not old_files:
            await update.message.reply_text(
                "✓ No old files to clean up.\n\n"
                "All voice files are recent.",
                parse_mode='Markdown'
            )
            return

        # Delete old files
        total_size = 0
        for file_path in old_files:
            total_size += os.path.getsize(file_path)
            os.remove(file_path)
            logger.info(f"Deleted old voice file: {file_path}")

        await update.message.reply_text(
            f"🗑️ **Cleanup complete**\n\n"
            f"Deleted {len(old_files)} old files\n"
            f"Freed {total_size / 1024:.1f} KB of disk space",
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Cleanup error: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Cleanup failed: {str(e)[:100]}",
            parse_mode='Markdown'
        )
```

Register the cleanup command in `main()`:

```python
app.add_handler(CommandHandler("cleanup", handle_cleanup))
```

#### Step 5.4: Update /help Command

Update the help text to mention voice functionality:

```python
async def handle_help(update: Update, context) -> None:
    """Handle /help command."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    help_message = (
        "**Claude Code Remote Assistant - Help**\n\n"
        "**How to Use:**\n\n"
        "1️⃣ **Voice Messages** ✓ Working\n"
        "   - Tap microphone icon in Telegram\n"
        "   - Speak your coding task clearly\n"
        "   - Bot will download and convert (transcription in Step 6)\n\n"
        "2️⃣ **Text Messages**\n"
        "   - Type your request directly\n"
        "   - Bot will process (Claude integration in Step 9)\n\n"
        "**Commands:**\n"
        "/start - Initialize bot\n"
        "/status - Check session info\n"
        "/clear - Reset conversation\n"
        "/cleanup - Delete old voice files\n"
        "/help - Show this help\n\n"
        "**Tips:**\n"
        "• Keep voice messages under 60 seconds\n"
        "• Speak clearly in a quiet environment\n"
        "• Use /cleanup periodically to free disk space\n\n"
        "**Current Status:**\n"
        "✓ Voice download & conversion working\n"
        "⏳ Transcription: Coming in Step 6\n"
        "⏳ Claude integration: Coming in Step 9"
    )

    await update.message.reply_text(
        help_message,
        parse_mode='Markdown'
    )
```

#### Step 5.5: Test Voice Processing

```bash
# Restart bot with changes
docker-compose restart telegram-bot

# Watch logs
docker-compose logs -f telegram-bot
```

**Test in Telegram:**

1. Open your bot in Telegram
2. Send `/start` to initialize
3. Tap the microphone icon
4. Record a short voice message (3-5 seconds): "Hello, this is a test"
5. Release to send

Expected bot response:
```
🎤 Voice message received

✓ Downloaded (5s, 12345 bytes)
✓ Converted to WAV (123456 bytes)

⏳ Transcription coming in Step 6...

Files saved:
• voice_123456789_20260204_143022.ogg
• voice_123456789_20260204_143022.wav
```

6. Check files were created:
```bash
docker exec telegram-bot ls -lh /app/sessions/voice_*
```

Expected output showing .ogg and .wav files.

### Code Examples

**Test Script for Voice Processing:**

```python
# test_voice_conversion.py
"""
Test voice file conversion without Telegram.
Useful for debugging ffmpeg issues.
"""

import subprocess
import sys

def test_conversion(input_file):
    """Test converting a voice file."""
    output_file = input_file.replace('.ogg', '.wav')

    print(f"Converting {input_file} → {output_file}")

    result = subprocess.run(
        [
            'ffmpeg',
            '-y',
            '-i', input_file,
            '-ar', '16000',
            '-ac', '1',
            '-acodec', 'pcm_s16le',
            output_file
        ],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print("✓ Conversion successful")
        # Print file info
        subprocess.run(['file', output_file])
        subprocess.run(['ffprobe', output_file], stderr=subprocess.DEVNULL)
    else:
        print("✗ Conversion failed")
        print(result.stderr)
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_voice_conversion.py <voice.ogg>")
        sys.exit(1)

    test_conversion(sys.argv[1])
```

**Validation Script:**

```bash
cat > validate_voice.sh << 'EOF'
#!/bin/bash
# Validate voice processing

echo "Validating Voice Processing (Step 5)..."
echo "======================================"

# Check ffmpeg is installed
if docker exec telegram-bot which ffmpeg > /dev/null 2>&1; then
    version=$(docker exec telegram-bot ffmpeg -version | head -1)
    echo "✓ ffmpeg installed: $version"
else
    echo "✗ ffmpeg not installed"
    exit 1
fi

# Check sessions directory is writable
if docker exec telegram-bot test -w /app/sessions; then
    echo "✓ Sessions directory is writable"
else
    echo "✗ Sessions directory not writable"
    exit 1
fi

# Check bot code has voice handler
if docker exec telegram-bot grep -q "async def handle_voice" bot.py; then
    echo "✓ Voice handler implemented"
else
    echo "✗ Voice handler not found"
    exit 1
fi

# Check subprocess import
if docker exec telegram-bot grep -q "import subprocess" bot.py; then
    echo "✓ subprocess module imported"
else
    echo "✗ subprocess not imported"
    exit 1
fi

echo ""
echo "======================================"
echo "✓ Voice processing validation passed"
echo ""
echo "Next steps:"
echo "1. Send a voice message to your bot"
echo "2. Check bot response shows download & conversion"
echo "3. Verify files created: docker exec telegram-bot ls sessions/"
echo "4. Proceed to Step 6: Deepgram API Integration"
EOF

chmod +x validate_voice.sh
./validate_voice.sh
```

### Project Structure

After this step:

```
claude-remote-runner/
├── bot/
│   ├── bot.py                  # ← UPDATED: Voice handler implemented
│   ├── config.py
│   └── requirements.txt
├── sessions/                   # Voice files stored here
│   ├── bot_data.pkl
│   ├── voice_123456789_20260204_143022.ogg  # ← NEW: Downloaded voice
│   └── voice_123456789_20260204_143022.wav  # ← NEW: Converted audio
├── validate_voice.sh           # ← NEW: Validation script
└── test_voice_conversion.py    # ← NEW: Test script
```

## Testing & Validation

### Test Cases

**Test 1: Short Voice Message (5 seconds)**
- Record: "Hello bot, this is a test"
- Expected: Download and convert successfully
- Check: Files created in sessions/

**Test 2: Long Voice Message (30 seconds)**
- Record: Longer message with multiple sentences
- Expected: Download and convert successfully
- Check: WAV file size proportional to duration

**Test 3: Multiple Voice Messages in Sequence**
- Send 3 voice messages back-to-back
- Expected: Each processed independently
- Check: 6 files created (3 OGG + 3 WAV)

**Test 4: Voice Message + Text Message**
- Send voice, then send text "hi"
- Expected: Both handled correctly
- Check: No interference between handlers

**Test 5: Cleanup Command**
- Send `/cleanup` command
- Expected: Old files deleted (if any >1 hour old)

**Test 6: Error Recovery**
- Stop ffmpeg in container
- Send voice message
- Expected: Error message, no crash

**Test 7: File Permissions**
```bash
docker exec telegram-bot ls -la sessions/voice_*
# Expected: Files are readable and writable
```

**Test 8: Conversion Quality**
```bash
# Check WAV file properties
docker exec telegram-bot ffprobe sessions/voice_*.wav
# Expected: 16kHz sample rate, mono, PCM format
```

### Acceptance Criteria

- [ ] Voice handler implemented in bot.py
- [ ] subprocess module imported
- [ ] Bot downloads voice messages from Telegram
- [ ] Files saved with unique timestamps
- [ ] ffmpeg converts OGG to WAV successfully
- [ ] WAV files are 16kHz, mono, PCM format
- [ ] Status messages update during processing
- [ ] Files stored in sessions/ directory
- [ ] File paths stored in context for later cleanup
- [ ] Error handling for download failures
- [ ] Error handling for conversion failures
- [ ] Timeout protection for ffmpeg (30 seconds)
- [ ] Cleanup command implemented (/cleanup)
- [ ] Help text updated to mention voice feature
- [ ] Logs show detailed processing steps
- [ ] No crashes on malformed voice messages
- [ ] validate_voice.sh passes all checks

### How to Test

**Complete Test Procedure:**

```bash
# 1. Validate prerequisites
./validate_voice.sh

# 2. Restart bot
docker-compose restart telegram-bot
docker-compose logs -f telegram-bot

# 3. Send test voice messages:
#    - Short message (5s)
#    - Medium message (15s)
#    - Long message (30s)

# 4. Check files created
docker exec telegram-bot ls -lh sessions/voice_*

# 5. Verify file formats
docker exec telegram-bot file sessions/voice_*.wav
# Expected: "RIFF (little-endian) data, WAVE audio"

docker exec telegram-bot ffprobe sessions/voice_*.wav 2>&1 | grep Stream
# Expected: "Stream #0:0: Audio: pcm_s16le, 16000 Hz, mono"

# 6. Check file sizes are reasonable
docker exec telegram-bot du -sh sessions/
# Should be manageable size

# 7. Test cleanup
# Send /cleanup in Telegram
docker exec telegram-bot ls -lh sessions/voice_*
# Old files should be removed

# 8. Test error handling
# (Temporarily rename ffmpeg to simulate failure)
docker exec telegram-bot mv /usr/bin/ffmpeg /usr/bin/ffmpeg.bak
# Send voice message
# Expected: Error message, no crash
# Restore ffmpeg
docker exec telegram-bot mv /usr/bin/ffmpeg.bak /usr/bin/ffmpeg
```

## Troubleshooting

### Issue 1: ffmpeg Not Found

**Symptoms:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'ffmpeg'
```

**Solutions:**

```bash
# Check if installed
docker exec telegram-bot which ffmpeg

# If not installed, update docker-compose.yml command:
apt-get install -y ffmpeg curl git

# Rebuild
docker-compose down
docker-compose up -d
```

### Issue 2: Permission Denied Writing to sessions/

**Symptoms:**
```
PermissionError: [Errno 13] Permission denied: '/app/sessions/voice_...'
```

**Solutions:**

```bash
# Fix permissions on host
chmod 777 sessions/

# Or in container
docker exec telegram-bot chmod 777 /app/sessions
```

### Issue 3: Conversion Timeout

**Symptoms:**
```
subprocess.TimeoutExpired: Command '['ffmpeg', ...]' timed out after 30 seconds
```

**Solutions:**

1. **Increase timeout:**
   ```python
   timeout=60  # Increase to 60 seconds
   ```

2. **Check CPU usage:**
   ```bash
   docker stats telegram-bot
   ```

3. **Test conversion manually:**
   ```bash
   docker exec telegram-bot ffmpeg -i sessions/voice.ogg -ar 16000 -ac 1 test.wav
   ```

### Issue 4: Invalid OGG File

**Symptoms:**
```
ffmpeg error: Invalid data found when processing input
```

**Solutions:**

1. **Check file was fully downloaded:**
   ```bash
   docker exec telegram-bot file sessions/voice_*.ogg
   # Should show "Ogg data"
   ```

2. **Re-download from Telegram:**
   - Send voice message again
   - Check network connection

3. **Add validation:**
   ```python
   if not os.path.exists(ogg_path) or os.path.getsize(ogg_path) == 0:
       raise ValueError("Downloaded file is empty or missing")
   ```

### Issue 5: Disk Space Full

**Symptoms:**
```
OSError: [Errno 28] No space left on device
```

**Solutions:**

1. **Check disk usage:**
   ```bash
   docker exec telegram-bot df -h
   ```

2. **Clean up old files:**
   ```bash
   docker exec telegram-bot find /app/sessions -name "voice_*" -mtime +1 -delete
   ```

3. **Implement automatic cleanup:**
   ```python
   # After successful conversion, delete OGG (keep WAV only)
   os.remove(ogg_path)
   ```

### Issue 6: WAV File Plays as Noise

**Symptoms:**
- WAV file exists but sounds like static/noise

**Solutions:**

1. **Check original OGG file:**
   ```bash
   docker exec telegram-bot ffplay sessions/voice_*.ogg
   ```

2. **Try different codec:**
   ```python
   '-acodec', 'pcm_s16le'  # Try pcm_s16be or libmp3lame
   ```

3. **Verify ffmpeg command:**
   ```bash
   # Test manually
   docker exec telegram-bot ffmpeg -i voice.ogg -ar 16000 -ac 1 -acodec pcm_s16le test.wav
   docker exec telegram-bot ffplay test.wav
   ```

## Rollback Procedure

### Revert to Placeholder Voice Handler

```python
async def handle_voice(update: Update, context) -> None:
    """Placeholder voice handler."""
    await update.message.reply_text(
        "🎤 Voice processing not yet implemented"
    )
```

### Remove Voice Files

```bash
# Delete all voice files
docker exec telegram-bot rm -f /app/sessions/voice_*

# Or on host
rm -f sessions/voice_*
```

### Restore Previous bot.py

```bash
git checkout HEAD~1 bot/bot.py
docker-compose restart telegram-bot
```

## Next Step

Once all acceptance criteria are met, proceed to:

**Step 6: Deepgram API Integration**
- File: `docs/implementation/step_06_whisper_integration.md`
- Duration: 1 hour
- Goal: Transcribe WAV files using Deepgram API

Before proceeding, ensure:
1. Voice messages download successfully
2. OGG files convert to WAV without errors
3. WAV files are 16kHz, mono, PCM format
4. Files are stored with unique filenames
5. Cleanup command works
6. validate_voice.sh passes all checks
7. No disk space issues

**Checkpoint:** Voice messages are now being downloaded and converted to the correct format. The next step will add transcription to convert these audio files into text.

**Save Your Work:**
```bash
git add bot/bot.py validate_voice.sh test_voice_conversion.py
git commit -m "Implement voice download & conversion (Step 5)

- Add voice message download from Telegram
- Implement OGG to WAV conversion using ffmpeg
- Convert to 16kHz mono PCM format (optimal for Whisper)
- Add unique filename generation with timestamps
- Implement /cleanup command for old files
- Add error handling for download/conversion failures
- Add 30-second timeout protection
- Update help text with voice feature
- Add validation and test scripts
- All tests passing"
```
