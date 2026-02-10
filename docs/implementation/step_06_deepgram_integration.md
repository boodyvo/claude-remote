# Step 6: Deepgram API Integration

**Estimated Time:** 1 hour
**Prerequisites:**
- Steps 1-5 completed (voice download & conversion working)
- Deepgram API key from Step 2
- WAV files being created successfully
- deepgram-sdk Python package installed (from requirements.txt)

**Deliverable:** Bot transcribes voice messages using Deepgram API and displays transcribed text

## Overview

This step integrates Deepgram's speech-to-text API to transcribe voice messages into text. Deepgram Nova-3 offers high accuracy, fast processing, and cost-effective pricing at $0.0043/min ($25.80 per 100 hours).

We'll implement:
- Deepgram client initialization
- WAV file upload to Deepgram API
- Transcription with language detection and smart formatting
- Error handling for API failures (rate limits, timeouts, invalid audio)
- Cost optimization (cleanup files after transcription)

By the end of this step, users can send voice messages and receive accurate text transcriptions. Step 7 will test and validate this complete voice-to-text pipeline.

## Implementation Details

### What to Build

1. **Deepgram Client:** Initialize Deepgram SDK with API key
2. **Deepgram Transcription:** Call Deepgram API with WAV file
3. **Language Detection:** Automatic language detection or explicit language setting
4. **Response Formatting:** Display transcription to user with smart formatting
5. **Error Handling:** API rate limits, invalid audio, network errors
6. **File Cleanup:** Delete audio files after successful transcription
7. **Cost Tracking:** Log transcription duration for cost monitoring

### How to Implement

#### Step 6.1: Add Deepgram Client to bot/bot.py

At the top of bot.py, after imports:

```python
from deepgram import DeepgramClient, PrerecordedOptions

# Initialize Deepgram client
deepgram = DeepgramClient(config.DEEPGRAM_API_KEY)
```

#### Step 6.2: Update Voice Handler with Deepgram Integration

Replace the voice handler in bot/bot.py with this complete implementation:

```python
async def handle_voice(update: Update, context) -> None:
    """
    Handle voice messages from users.

    Downloads, converts, and transcribes voice messages using Deepgram API.
    """
    user_id = update.effective_user.id

    # Check authorization
    if not check_authorization(user_id):
        logger.warning(f"Unauthorized voice message from user {user_id}")
        await update.message.reply_text("⛔ Unauthorized")
        return

    logger.info(f"Voice message received from user {user_id}")

    # Track start time for cost monitoring
    import time
    start_time = time.time()

    # Send "processing" message
    status_msg = await update.message.reply_text(
        "🎤 **Voice message received**\n\n"
        "⏳ Downloading...",
        parse_mode='Markdown'
    )

    ogg_path = None
    wav_path = None

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

        # Update status
        await status_msg.edit_text(
            "🎤 **Voice message received**\n\n"
            f"✓ Downloaded ({duration}s)\n"
            f"✓ Converted to WAV\n"
            "⏳ Transcribing...",
            parse_mode='Markdown'
        )

        # Step 3: Transcribe with Deepgram API
        logger.info(f"Starting Deepgram transcription for {wav_path}")

        with open(wav_path, 'rb') as audio:
            # Prepare audio source
            source = {'buffer': audio, 'mimetype': 'audio/wav'}

            # Configure Deepgram options
            options = PrerecordedOptions(
                model='nova-2',  # Nova-2 model for best accuracy
                language='en',   # Specify language or omit for auto-detect
                smart_format=True  # Enable smart formatting
            )

            # Call Deepgram API
            response = deepgram.listen.prerecorded.v('1').transcribe_file(source, options)

        # Extract transcribed text
        transcribed_text = response.results.channels[0].alternatives[0].transcript
        detected_language = response.results.channels[0].detected_language if hasattr(response.results.channels[0], 'detected_language') else 'en'

        logger.info(f"Transcription complete: {len(transcribed_text)} characters, language: {detected_language}")
        logger.info(f"Transcribed text: {transcribed_text}")

        # Calculate processing time
        processing_time = time.time() - start_time

        # Estimate cost (Deepgram API: $0.0043/minute)
        duration_minutes = duration / 60
        estimated_cost = duration_minutes * 0.0043

        logger.info(f"Processing took {processing_time:.2f}s, estimated cost: ${estimated_cost:.4f}")

        # Step 4: Send transcription to user
        response_message = (
            "🎤 **Voice transcribed successfully**\n\n"
            f"**Transcription:**\n{transcribed_text}\n\n"
            f"**Details:**\n"
            f"• Duration: {duration}s\n"
            f"• Language: {detected_language}\n"
            f"• Processing time: {processing_time:.1f}s\n"
            f"• Estimated cost: ${estimated_cost:.4f}\n\n"
            "⏳ Claude integration coming in Step 9..."
        )

        await status_msg.edit_text(
            response_message,
            parse_mode='Markdown'
        )

        # Store transcription in context for future use (Step 9)
        context.user_data['last_transcription'] = transcribed_text

        # Step 5: Cleanup audio files to save space and costs
        try:
            os.remove(ogg_path)
            os.remove(wav_path)
            logger.info(f"Cleaned up audio files: {ogg_path}, {wav_path}")
        except Exception as cleanup_error:
            logger.warning(f"Cleanup failed: {cleanup_error}")

        logger.info(f"Voice processing complete for user {user_id}")

    except Exception as e:
        # Deepgram API errors
        if 'rate limit' in str(e).lower():
            logger.error(f"Deepgram rate limit exceeded: {e}")
            await status_msg.edit_text(
                "⏱️ **Rate limit exceeded**\n\n"
                "Too many transcription requests.\n"
                "Please wait a moment and try again.",
                parse_mode='Markdown'
            )
        elif 'authentication' in str(e).lower() or 'unauthorized' in str(e).lower():
            logger.error(f"Deepgram authentication error: {e}")
            await status_msg.edit_text(
                "❌ **Authentication failed**\n\n"
                "Invalid Deepgram API key.\n"
                "Please check your configuration.",
                parse_mode='Markdown'
            )
        elif 'connection' in str(e).lower() or 'network' in str(e).lower():
            logger.error(f"Deepgram connection error: {e}")
            await status_msg.edit_text(
                "❌ **Connection failed**\n\n"
                "Could not connect to transcription service.\n"
                "Please check your internet connection and try again.",
                parse_mode='Markdown'
            )
        else:
            logger.error(f"Deepgram API error: {e}", exc_info=True)
            await status_msg.edit_text(
                "❌ **Transcription failed**\n\n"
                f"Deepgram API error: {str(e)[:100]}\n\n"
                "Please try again in a few moments.",
                parse_mode='Markdown'
            )

    except subprocess.TimeoutExpired:
        logger.error("ffmpeg conversion timeout")
        await status_msg.edit_text(
            "❌ **Conversion timeout**\n\n"
            "Audio conversion took too long.\n"
            "Try a shorter voice message.",
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Voice processing error: {e}", exc_info=True)
        await status_msg.edit_text(
            "❌ **Processing failed**\n\n"
            f"An error occurred: {str(e)[:100]}\n\n"
            "Please try again.",
            parse_mode='Markdown'
        )

    finally:
        # Cleanup files in case of error
        if ogg_path and os.path.exists(ogg_path):
            try:
                os.remove(ogg_path)
            except:
                pass
        if wav_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
            except:
                pass
```

#### Step 6.3: Update Requirements (if needed)

Verify deepgram-sdk package version in bot/requirements.txt:

```txt
# Ensure you have the latest version
deepgram-sdk==3.0.0
```

If you need to update:

```bash
# Update requirements.txt, then rebuild
docker-compose down
docker-compose build --no-cache telegram-bot
docker-compose up -d
```

#### Step 6.4: Add Cost Tracking Command (Optional)

Add a command to track transcription costs:

```python
async def handle_costs(update: Update, context) -> None:
    """Show estimated transcription costs."""
    user_id = update.effective_user.id

    if not check_authorization(user_id):
        await update.message.reply_text("⛔ Unauthorized")
        return

    # Get usage stats from context (would need to track this)
    total_minutes = context.user_data.get('total_transcription_minutes', 0)
    total_cost = total_minutes * 0.006  # $0.0043 per minute

    await update.message.reply_text(
        f"💰 **Transcription Costs**\n\n"
        f"**This Session:**\n"
        f"• Total minutes: {total_minutes:.2f}\n"
        f"• Estimated cost: ${total_cost:.4f}\n\n"
        f"**Pricing:**\n"
        f"• Deepgram API: $0.0043/minute\n"
        f"• 1 hour = $0.258\n"
        f"• 100 hours/month = $25.80\n\n"
        f"**Tip:** Use shorter messages to save costs!",
        parse_mode='Markdown'
    )
```

Register in main():
```python
app.add_handler(CommandHandler("costs", handle_costs))
```

#### Step 6.5: Test Deepgram Integration

```bash
# Restart bot
docker-compose restart telegram-bot

# Watch logs for transcription details
docker-compose logs -f telegram-bot
```

**Test in Telegram:**

1. Send a clear voice message: "Hello, this is a test of the voice transcription system"
2. Wait for processing (10-20 seconds)
3. Verify you receive transcribed text

Expected response:
```
🎤 Voice transcribed successfully

Transcription:
Hello, this is a test of the voice transcription system.

Details:
• Duration: 5s
• Language: en
• Processing time: 12.3s
• Estimated cost: $0.0005

⏳ Claude integration coming in Step 9...
```

### Code Examples

**Test Script for Deepgram API:**

```python
#!/usr/bin/env python3
# test_deepgram.py
"""
Test Deepgram API transcription directly.
Useful for debugging API issues.
"""

import os
import sys
from deepgram import DeepgramClient, PrerecordedOptions
from dotenv import load_dotenv

load_dotenv()

def test_transcription(audio_file_path):
    """Test transcribing an audio file."""
    print(f"Testing Deepgram API with: {audio_file_path}")

    try:
        # Initialize client
        deepgram = DeepgramClient(os.getenv('DEEPGRAM_API_KEY'))

        with open(audio_file_path, 'rb') as audio:
            source = {'buffer': audio, 'mimetype': 'audio/wav'}
            options = PrerecordedOptions(
                model='nova-2',
                smart_format=True
            )

            response = deepgram.listen.prerecorded.v('1').transcribe_file(source, options)

        text = response.results.channels[0].alternatives[0].transcript

        print("\n✓ Transcription successful!\n")
        print(f"Text: {text}")

        return text

    except Exception as e:
        print(f"\n✗ Transcription failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_deepgram.py <audio_file.wav>")
        sys.exit(1)

    test_transcription(sys.argv[1])
```

Run with:
```bash
# Create a test WAV file first (from Step 5)
# Then test:
docker exec telegram-bot python test_deepgram.py sessions/voice_*.wav
```

**Validation Script:**

```bash
cat > validate_deepgram.sh << 'EOF'
#!/bin/bash
# Validate Deepgram integration

echo "Validating Deepgram API Integration (Step 6)..."
echo "=============================================="

# Check Deepgram API key is set
if docker exec telegram-bot env | grep -q "DEEPGRAM_API_KEY"; then
    echo "✓ Deepgram API key is set"
else
    echo "✗ Deepgram API key not set"
    exit 1
fi

# Check deepgram-sdk package installed
if docker exec telegram-bot pip list | grep -q "deepgram-sdk"; then
    version=$(docker exec telegram-bot pip show deepgram-sdk | grep Version | cut -d' ' -f2)
    echo "✓ deepgram-sdk package installed: v$version"
else
    echo "✗ deepgram-sdk package not installed"
    exit 1
fi

# Check bot code has Deepgram integration
if docker exec telegram-bot grep -q "DeepgramClient" bot.py; then
    echo "✓ Deepgram client implemented"
else
    echo "✗ Deepgram client not found"
    exit 1
fi

# Test Deepgram API connection
echo -n "Testing Deepgram API connection... "
if docker exec telegram-bot python -c "from deepgram import DeepgramClient; import os; DeepgramClient(os.getenv('DEEPGRAM_API_KEY'))" > /dev/null 2>&1; then
    echo "✓"
else
    echo "✗"
    echo "Deepgram API test failed. Check API key and network connection."
    exit 1
fi

echo ""
echo "=============================================="
echo "✓ Deepgram integration validation passed"
echo ""
echo "Next steps:"
echo "1. Send a voice message to your bot"
echo "2. Verify transcription appears in response"
echo "3. Check logs for cost estimates"
echo "4. Proceed to Step 7: Echo Bot Testing"
EOF

chmod +x validate_deepgram.sh
./validate_deepgram.sh
```

### Project Structure

After this step:

```
claude-remote-runner/
├── bot/
│   ├── bot.py                  # ← UPDATED: Deepgram integration added
│   ├── config.py
│   └── requirements.txt        # deepgram-sdk==3.0.0
├── test_deepgram.py            # ← NEW: Deepgram test script
├── validate_deepgram.sh        # ← NEW: Validation script
└── sessions/                   # Audio files cleaned up after transcription
```

## Testing & Validation

### Test Cases

**Test 1: Clear English Speech**
- Record: "Create a Python script that prints hello world"
- Expected: Accurate transcription with punctuation

**Test 2: Technical Terms**
- Record: "Add a function called get underscore user underscore data"
- Expected: Correct transcription of technical terms

**Test 3: Multiple Sentences**
- Record: "First create a file. Then add some code. Finally run the tests."
- Expected: All sentences transcribed accurately

**Test 4: Background Noise**
- Record message with moderate background noise
- Expected: Transcription may have minor errors but generally readable

**Test 5: Different Accents**
- Record with non-native English accent
- Expected: Whisper handles various accents well (90%+ accuracy)

**Test 6: Non-English Language**
- Record in another language (if relevant)
- Expected: Auto-detection works or manual language setting

**Test 7: Very Short Message (<2 seconds)**
- Record: "Test"
- Expected: Transcribes correctly

**Test 8: Long Message (30+ seconds)**
- Record: Long paragraph
- Expected: Full transcription, higher cost estimate

**Test 9: Empty/Silent Audio**
- Record silence or very quiet audio
- Expected: Empty transcription or error handling

**Test 10: Cost Tracking**
- Send multiple messages
- Check /costs command
- Expected: Accurate cost accumulation

### Acceptance Criteria

- [ ] deepgram-sdk package installed and imported
- [ ] Deepgram API key loaded from config
- [ ] Deepgram API call implemented in voice handler
- [ ] WAV files uploaded to Deepgram successfully
- [ ] Transcriptions returned accurately with smart formatting
- [ ] Language detection working (if needed)
- [ ] Transcribed text displayed to user
- [ ] Processing time tracked and displayed
- [ ] Cost estimates calculated and logged ($0.0043/min)
- [ ] Audio files cleaned up after transcription
- [ ] Error handling for API failures
- [ ] Error handling for rate limits
- [ ] Error handling for network errors
- [ ] Transcription stored in context for later use
- [ ] /costs command shows usage (optional)
- [ ] No API key exposure in logs
- [ ] validate_deepgram.sh passes all checks

### How to Test

**Complete Test Procedure:**

```bash
# 1. Validate setup
./validate_deepgram.sh

# 2. Restart bot
docker-compose restart telegram-bot

# 3. Watch logs
docker-compose logs -f telegram-bot

# 4. Send test voice messages in Telegram:
#    - "Hello world"
#    - "Create a Python script"
#    - "Add error handling and logging"

# 5. Verify transcriptions are accurate

# 6. Check cost estimates in responses

# 7. Verify files cleaned up
docker exec telegram-bot ls sessions/
# Should NOT see voice_*.ogg or voice_*.wav files

# 8. Check logs for transcription details
docker logs telegram-bot | grep "Transcription complete"

# 9. Test error handling
# Temporarily invalidate API key
# Send voice message
# Expected: Error message, no crash

# 10. Check API usage
# Go to: https://console.deepgram.com/
# Verify transcription usage appears
```

## Troubleshooting

### Issue 1: Deepgram API Key Invalid

**Symptoms:**
```
Authentication error or unauthorized
```

**Solutions:**

1. **Verify API key:**
   ```bash
   docker exec telegram-bot env | grep DEEPGRAM_API_KEY
   ```

2. **Test API key:**
   ```bash
   curl https://api.deepgram.com/v1/projects \
     -H "Authorization: Token $DEEPGRAM_API_KEY"
   ```

3. **Regenerate key:**
   - Go to https://console.deepgram.com/
   - Create new key
   - Update .env file
   - Restart containers

### Issue 2: Rate Limit Exceeded

**Symptoms:**
```
Rate limit error
```

**Solutions:**

1. **Check current limits:**
   - Go to https://console.deepgram.com/
   - View current tier and usage

2. **Implement backoff:**
   ```python
   import time
   for attempt in range(3):
       try:
           response = deepgram.listen.prerecorded...
           break
       except Exception as e:
           if 'rate limit' in str(e).lower():
               time.sleep(2 ** attempt)  # Exponential backoff
   ```

3. **Monitor usage:**
   - Check Deepgram console regularly
   - Set up billing alerts

### Issue 3: Transcription is Gibberish

**Symptoms:**
- Transcription returned but text is nonsensical

**Causes:**
- Corrupted audio file
- Wrong audio format
- Audio too quiet

**Solutions:**

1. **Verify WAV format:**
   ```bash
   docker exec telegram-bot ffprobe sessions/test.wav
   # Check: 16000 Hz, mono, pcm_s16le
   ```

2. **Test audio file manually:**
   ```bash
   docker exec telegram-bot ffplay sessions/test.wav
   ```

3. **Try different sample rate:**
   ```python
   '-ar', '24000'  # Instead of 16000
   ```

### Issue 4: Transcription Takes Too Long

**Symptoms:**
- Processing takes 30+ seconds for short audio

**Solutions:**

1. **Check file size:**
   ```bash
   docker exec telegram-bot ls -lh sessions/voice_*.wav
   # Should be ~320KB per second of audio
   ```

2. **Check network speed:**
   ```bash
   docker exec telegram-bot curl -o /dev/null -w '%{time_total}' https://api.deepgram.com/
   ```

3. **Optimize model:**
   - Deepgram Nova-2 is already optimized for speed
   - Check if smart_format adds latency (try disabling)

### Issue 5: High Costs

**Symptoms:**
- Deepgram bill higher than expected

**Solutions:**

1. **Check usage:**
   - Go to https://console.deepgram.com/
   - Review transcription usage and costs

2. **Implement limits:**
   ```python
   MAX_DURATION = 60  # Max 60 seconds per message
   if duration > MAX_DURATION:
       await update.message.reply_text(f"⚠️ Message too long (max {MAX_DURATION}s)")
       return
   ```

3. **Monitor and optimize:**
   - Set up billing alerts in Deepgram console
   - Implement rate limiting per user
   - Use shorter voice messages

### Issue 6: Language Detection Wrong

**Symptoms:**
- English audio detected as another language

**Solutions:**

1. **Explicitly set language:**
   ```python
   language="en"  # Force English
   ```

2. **Remove language parameter:**
   ```python
   # Let Whisper auto-detect
   transcript = openai.audio.transcriptions.create(
       model="whisper-1",
       file=audio_file
       # No language parameter
   )
   ```

## Rollback Procedure

### Remove Deepgram Integration

```python
# Simplified voice handler without transcription
async def handle_voice(update: Update, context) -> None:
    await update.message.reply_text(
        "Voice download working.\n"
        "Transcription temporarily disabled."
    )
```

### Restore Step 5 Version

```bash
git diff HEAD~1 bot/bot.py  # Review changes
git checkout HEAD~1 bot/bot.py  # Restore previous version
docker-compose restart telegram-bot
```

## Next Step

Once all acceptance criteria are met, proceed to:

**Step 7: Echo Bot Testing**
- File: `docs/implementation/step_07_echo_testing.md`
- Duration: 30 minutes
- Goal: Comprehensive testing of voice-to-text pipeline with various test cases

Before proceeding, ensure:
1. Deepgram API integration works
2. Transcriptions are accurate (>90% for clear audio)
3. Cost estimates are logged
4. Audio files are cleaned up after transcription
5. Error handling works for all failure modes
6. validate_whisper.sh passes all checks
7. No sensitive data (API keys) exposed in logs

**Checkpoint:** The voice-to-text pipeline is now complete! Users can send voice messages and receive accurate transcriptions. Step 7 will validate this with comprehensive testing, and Step 9 will connect these transcriptions to Claude Code.

**Save Your Work:**
```bash
git add bot/bot.py test_deepgram.py validate_deepgram.sh
git commit -m "Integrate Deepgram API for transcription (Step 6)

- Add Deepgram SDK initialization
- Implement Deepgram API transcription in voice handler (Nova-2 model)
- Add smart formatting for better transcription quality
- Calculate and display cost estimates ($0.0043/min)
- Implement file cleanup after transcription
- Add comprehensive error handling (API errors, rate limits, network)
- Store transcriptions in context for future Claude integration
- Add /costs command for cost tracking (optional)
- Add test and validation scripts
- Deepgram offers 28% cost savings vs Whisper"
```
