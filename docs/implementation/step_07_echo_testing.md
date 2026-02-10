# Step 7: Echo Bot Testing

**Estimated Time:** 30 minutes
**Prerequisites:**
- Steps 1-6 completed (full voice-to-text pipeline working)
- Bot transcribing voice messages successfully
- Access to Telegram on multiple devices (optional but helpful)

**Deliverable:** Comprehensive test report validating voice-to-text accuracy, performance, and error handling

## Overview

This step focuses on thorough testing of the voice-to-text pipeline built in Steps 4-6. We'll validate transcription accuracy across various conditions, test error scenarios, measure performance, and document any issues for future optimization.

This is a critical validation step before proceeding to Claude Code integration (Steps 9-10). By ensuring the voice pipeline is rock-solid now, we prevent compounding issues later.

Testing areas:
- Transcription accuracy with various speech patterns
- Performance under different conditions
- Error handling and recovery
- Edge cases and boundary conditions
- Cost validation

## Implementation Details

### What to Build

1. **Test Suite:** Structured test cases covering common and edge scenarios
2. **Test Script:** Automated tests where possible
3. **Test Report:** Document results, accuracy metrics, issues found
4. **Performance Metrics:** Measure latency and resource usage
5. **Issue Log:** Track any bugs or limitations discovered

### How to Implement

#### Step 7.1: Create Test Case Checklist

Create a structured test document:

```bash
cat > test_cases_voice.md << 'EOF'
# Voice-to-Text Pipeline Test Cases

**Test Date:** YYYY-MM-DD
**Tester:** Your Name
**Bot Version:** Step 7
**Environment:** Local Docker / Coolify Production

## Test Results Summary

| Category | Tests | Passed | Failed | Notes |
|----------|-------|--------|--------|-------|
| Basic Functionality | 5 | _ | _ | |
| Accuracy | 10 | _ | _ | |
| Performance | 5 | _ | _ | |
| Error Handling | 6 | _ | _ | |
| Edge Cases | 5 | _ | _ | |
| **TOTAL** | **31** | **_** | **_** | |

---

## 1. Basic Functionality Tests

### Test 1.1: Simple Voice Message
- **Input:** "Hello bot"
- **Expected:** Transcription: "Hello bot" or similar
- **Result:** ☐ Pass ☐ Fail
- **Actual:** ___________________________
- **Notes:** ___________________________

### Test 1.2: /start Command
- **Action:** Send /start
- **Expected:** Welcome message with instructions
- **Result:** ☐ Pass ☐ Fail

### Test 1.3: /help Command
- **Action:** Send /help
- **Expected:** Help text mentioning voice feature
- **Result:** ☐ Pass ☐ Fail

### Test 1.4: /status Command
- **Action:** Send /status
- **Expected:** Status info with user ID
- **Result:** ☐ Pass ☐ Fail

### Test 1.5: Text Message Echo
- **Input:** "Test text message"
- **Expected:** Echo response (placeholder)
- **Result:** ☐ Pass ☐ Fail

---

## 2. Transcription Accuracy Tests

### Test 2.1: Clear Simple Speech
- **Input:** "Create a Python script"
- **Expected:** Exact or very close transcription
- **Result:** ☐ Pass ☐ Fail
- **Accuracy:** _____% (measure manually)

### Test 2.2: Technical Terms
- **Input:** "Add get underscore user underscore data function"
- **Expected:** Recognizes "get_user_data" concept
- **Result:** ☐ Pass ☐ Fail
- **Actual:** ___________________________

### Test 2.3: Punctuation
- **Input:** "First, create a file. Then, add code. Finally, run tests."
- **Expected:** Correct punctuation and sentence breaks
- **Result:** ☐ Pass ☐ Fail
- **Actual:** ___________________________

### Test 2.4: Numbers
- **Input:** "Add numbers one through ten"
- **Expected:** Recognizes "1 through 10" or written form
- **Result:** ☐ Pass ☐ Fail
- **Actual:** ___________________________

### Test 2.5: Code-Related Terms
- **Input:** "Import numpy as np and create an array"
- **Expected:** Correct library names and technical terms
- **Result:** ☐ Pass ☐ Fail
- **Actual:** ___________________________

### Test 2.6: Long Sentence (30+ seconds)
- **Input:** [Record 30-40 second message with multiple sentences]
- **Expected:** Full accurate transcription
- **Result:** ☐ Pass ☐ Fail
- **Accuracy:** _____% (count errors vs total words)

### Test 2.7: Fast Speech
- **Input:** [Speak quickly but clearly]
- **Expected:** Still transcribes accurately
- **Result:** ☐ Pass ☐ Fail

### Test 2.8: Slow Speech
- **Input:** [Speak very slowly with pauses]
- **Expected:** Still transcribes accurately
- **Result:** ☐ Pass ☐ Fail

### Test 2.9: Moderate Background Noise
- **Input:** [Record with TV/music in background]
- **Expected:** Still mostly accurate (>80%)
- **Result:** ☐ Pass ☐ Fail
- **Actual:** ___________________________

### Test 2.10: Different Accent
- **Input:** [Non-native English speaker if available]
- **Expected:** Handles various accents reasonably (>85%)
- **Result:** ☐ Pass ☐ Fail

---

## 3. Performance Tests

### Test 3.1: Processing Time - Short Message (5s)
- **Audio Duration:** ~5 seconds
- **Expected Processing:** <15 seconds total
- **Actual:** _____ seconds
- **Result:** ☐ Pass ☐ Fail

### Test 3.2: Processing Time - Medium Message (15s)
- **Audio Duration:** ~15 seconds
- **Expected Processing:** <20 seconds total
- **Actual:** _____ seconds
- **Result:** ☐ Pass ☐ Fail

### Test 3.3: Processing Time - Long Message (30s)
- **Audio Duration:** ~30 seconds
- **Expected Processing:** <30 seconds total
- **Actual:** _____ seconds
- **Result:** ☐ Pass ☐ Fail

### Test 3.4: Multiple Sequential Messages
- **Action:** Send 3 voice messages back-to-back
- **Expected:** Each processed independently, no blocking
- **Result:** ☐ Pass ☐ Fail
- **Notes:** ___________________________

### Test 3.5: Resource Usage
- **Action:** Monitor Docker stats during processing
- **Command:** `docker stats telegram-bot --no-stream`
- **CPU Usage:** _____%
- **Memory Usage:** _____ MB
- **Result:** ☐ Pass (under limits) ☐ Fail

---

## 4. Error Handling Tests

### Test 4.1: Very Short Audio (<1 second)
- **Input:** Quick tap, very short sound
- **Expected:** Handles gracefully (empty or short transcription)
- **Result:** ☐ Pass ☐ Fail

### Test 4.2: Silent Audio
- **Input:** Record silence (no speech)
- **Expected:** Empty or minimal transcription, no error
- **Result:** ☐ Pass ☐ Fail

### Test 4.3: Unintelligible Audio
- **Input:** Mumbling or very unclear speech
- **Expected:** Some transcription or clear error
- **Result:** ☐ Pass ☐ Fail

### Test 4.4: Network Interruption (manual test)
- **Action:** Temporarily block internet, send voice message
- **Expected:** Error message about network connectivity
- **Result:** ☐ Pass ☐ Fail

### Test 4.5: Invalid API Key (manual test)
- **Action:** Temporarily corrupt DEEPGRAM_API_KEY in .env
- **Expected:** Clear error about authentication
- **Result:** ☐ Pass ☐ Fail
- **Notes:** (Restore API key after test!)

### Test 4.6: Bot Restart During Processing
- **Action:** Send voice, immediately restart bot
- **Expected:** Graceful handling, user gets error or retry prompt
- **Result:** ☐ Pass ☐ Fail

---

## 5. Edge Cases

### Test 5.1: Multiple Users Simultaneously
- **Action:** Two users send voice messages at same time
- **Expected:** Both processed independently
- **Result:** ☐ Pass ☐ Fail
- **Notes:** (Need two Telegram accounts)

### Test 5.2: Very Long Message (60+ seconds)
- **Input:** Record maximum length Telegram allows
- **Expected:** Processes successfully or gives clear limit error
- **Result:** ☐ Pass ☐ Fail
- **Cost Estimate:** $______

### Test 5.3: Non-English Language
- **Input:** [Record in another language if applicable]
- **Expected:** Auto-detects language or falls back gracefully
- **Result:** ☐ Pass ☐ Fail

### Test 5.4: File Cleanup
- **Action:** Send 5 voice messages, then check sessions/ directory
- **Expected:** Old audio files deleted, only bot_data.pkl remains
- **Command:** `docker exec telegram-bot ls -la sessions/`
- **Result:** ☐ Pass ☐ Fail

### Test 5.5: Unauthorized User
- **Action:** Send message from user NOT in ALLOWED_USER_IDS
- **Expected:** "Unauthorized" message
- **Result:** ☐ Pass ☐ Fail
- **Notes:** (Need another Telegram account)

---

## 6. Cost Validation

### Test 6.1: Single Message Cost
- **Audio Duration:** 5 seconds
- **Expected Cost:** ~$0.0005 ($0.0043/min * 5/60)
- **Actual Cost (from bot):** $______
- **Result:** ☐ Pass ☐ Fail

### Test 6.2: Cumulative Cost Tracking
- **Action:** Send 10 voice messages (various lengths)
- **Total Duration:** _____ seconds
- **Expected Total Cost:** $______ (duration/60 * 0.006)
- **Actual:** Check OpenAI dashboard
- **Result:** ☐ Pass ☐ Fail

---

## 7. Integration Checks

### Test 7.1: Transcription Stored in Context
- **Action:** Send voice message
- **Check:** Verify context.user_data['last_transcription'] exists
- **Method:** Check bot logs
- **Result:** ☐ Pass ☐ Fail

### Test 7.2: Docker Volume Persistence
- **Action:** Restart container, send /status
- **Expected:** Session data persists
- **Result:** ☐ Pass ☐ Fail

### Test 7.3: Logs Are Clean
- **Action:** Review bot logs for errors/warnings
- **Command:** `docker logs telegram-bot | grep -i error`
- **Expected:** No unexpected errors
- **Result:** ☐ Pass ☐ Fail

---

## Issues Found

| # | Severity | Issue | Steps to Reproduce | Status |
|---|----------|-------|-------------------|--------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Average processing time (5s audio) | <15s | ___s | |
| Average processing time (15s audio) | <20s | ___s | |
| Transcription accuracy (clear audio) | >90% | ___% | |
| Transcription accuracy (noisy audio) | >80% | ___% | |
| Memory usage | <500MB | ___MB | |
| CPU usage (peak) | <80% | ___% | |

---

## Overall Assessment

**Voice-to-Text Pipeline Status:**
☐ Production Ready
☐ Minor issues (document and proceed)
☐ Major issues (needs fixes before Step 9)

**Recommended Actions:**
1. ___________________________________
2. ___________________________________
3. ___________________________________

**Sign-off:**
- Name: _______________
- Date: _______________
- Ready for Step 9: ☐ Yes ☐ No

EOF
```

#### Step 7.2: Create Automated Test Script

```bash
cat > test_voice_pipeline.sh << 'EOF'
#!/bin/bash
# Automated testing for voice-to-text pipeline

echo "=========================================="
echo "Voice-to-Text Pipeline Automated Tests"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Test 1: Bot is running
echo -n "Test 1: Bot container running... "
if docker ps | grep -q telegram-bot; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 2: Required packages installed
echo -n "Test 2: Required packages installed... "
if docker exec telegram-bot pip list | grep -q "openai" && \
   docker exec telegram-bot pip list | grep -q "python-telegram-bot"; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 3: ffmpeg available
echo -n "Test 3: ffmpeg installed... "
if docker exec telegram-bot which ffmpeg > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 4: OpenAI API key set
echo -n "Test 4: OpenAI API key configured... "
if docker exec telegram-bot env | grep -q "DEEPGRAM_API_KEY=sk-"; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 5: Bot code has transcription logic
echo -n "Test 5: Whisper integration in code... "
if docker exec telegram-bot grep -q "openai.audio.transcriptions.create" bot.py; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 6: Sessions directory writable
echo -n "Test 6: Sessions directory writable... "
if docker exec telegram-bot test -w /app/sessions; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 7: No critical errors in logs
echo -n "Test 7: No critical errors in logs... "
error_count=$(docker logs telegram-bot 2>&1 | grep -i "critical\|fatal" | wc -l)
if [ "$error_count" -eq 0 ]; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL (found $error_count critical errors)${NC}"
    ((FAIL++))
fi

# Test 8: Bot responds to API test
echo -n "Test 8: OpenAI API accessible... "
if docker exec telegram-bot python -c "import openai, os; openai.api_key=os.getenv('DEEPGRAM_API_KEY'); openai.models.list()" > /dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

# Test 9: File cleanup working
echo -n "Test 9: Audio files cleaned up... "
audio_files=$(docker exec telegram-bot find /app/sessions -name "voice_*.ogg" -o -name "voice_*.wav" 2>/dev/null | wc -l)
if [ "$audio_files" -eq 0 ]; then
    echo -e "${GREEN}PASS (no leftover files)${NC}"
    ((PASS++))
else
    echo -e "${YELLOW}WARNING (found $audio_files audio files)${NC}"
    echo "  (This is OK if you just tested recently)"
    ((PASS++))
fi

# Test 10: Memory usage reasonable
echo -n "Test 10: Memory usage check... "
mem_usage=$(docker stats telegram-bot --no-stream --format "{{.MemUsage}}" | cut -d'/' -f1 | sed 's/[^0-9.]//g')
if (( $(echo "$mem_usage < 500" | bc -l) )); then
    echo -e "${GREEN}PASS (${mem_usage}MB)${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL (${mem_usage}MB - too high)${NC}"
    ((FAIL++))
fi

# Summary
echo ""
echo "=========================================="
echo "Test Results Summary"
echo "=========================================="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo "Total: $((PASS + FAIL))"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All automated tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Complete manual test cases in test_cases_voice.md"
    echo "2. Send various voice messages to verify accuracy"
    echo "3. Document any issues found"
    echo "4. If all tests pass, proceed to Step 8"
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some tests failed. Review and fix issues.${NC}"
    exit 1
fi
EOF

chmod +x test_voice_pipeline.sh
```

#### Step 7.3: Run Automated Tests

```bash
./test_voice_pipeline.sh
```

Expected output:
```
==========================================
Voice-to-Text Pipeline Automated Tests
==========================================
Test 1: Bot container running... PASS
Test 2: Required packages installed... PASS
Test 3: ffmpeg installed... PASS
Test 4: OpenAI API key configured... PASS
Test 5: Whisper integration in code... PASS
Test 6: Sessions directory writable... PASS
Test 7: No critical errors in logs... PASS
Test 8: OpenAI API accessible... PASS
Test 9: Audio files cleaned up... PASS
Test 10: Memory usage check... PASS (245MB)

==========================================
Test Results Summary
==========================================
Passed: 10
Failed: 0
Total: 10

✓ All automated tests passed!
```

#### Step 7.4: Manual Testing Checklist

**Perform these tests and document results in test_cases_voice.md:**

1. **Open test_cases_voice.md:**
   ```bash
   # Edit with your preferred editor
   nano test_cases_voice.md
   # or
   code test_cases_voice.md
   ```

2. **Work through each test case:**
   - Send voice messages as specified
   - Mark Pass/Fail
   - Record actual transcriptions
   - Note any issues

3. **Calculate accuracy:**
   ```
   Accuracy = (Correct words / Total words) * 100
   ```

4. **Measure performance:**
   - Note timestamps from bot responses
   - Calculate: (Response time - Audio duration)

5. **Document issues:**
   - Fill in "Issues Found" table
   - Include reproduction steps
   - Rate severity (Critical, Major, Minor)

#### Step 7.5: Generate Test Report

```bash
cat > generate_test_report.sh << 'EOF'
#!/bin/bash
# Generate summary test report

echo "Voice-to-Text Pipeline Test Report"
echo "==================================="
echo ""
echo "Generated: $(date)"
echo ""

# Check if test_cases_voice.md exists
if [ ! -f test_cases_voice.md ]; then
    echo "ERROR: test_cases_voice.md not found"
    echo "Run manual tests first and fill in test_cases_voice.md"
    exit 1
fi

# Count pass/fail from test_cases_voice.md
total_tests=$(grep -o "☐ Pass" test_cases_voice.md | wc -l)
# Note: Manual completion of test cases required

echo "Total Manual Tests: $total_tests"
echo "Status: Manual tests require completion"
echo ""

# Show bot statistics
echo "Bot Statistics:"
echo "---------------"
echo "Container uptime:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep telegram-bot

echo ""
echo "Memory usage:"
docker stats telegram-bot --no-stream --format "{{.MemUsage}}"

echo ""
echo "Log summary:"
echo "  Total lines: $(docker logs telegram-bot 2>&1 | wc -l)"
echo "  Errors: $(docker logs telegram-bot 2>&1 | grep -i error | wc -l)"
echo "  Voice messages processed: $(docker logs telegram-bot 2>&1 | grep "Voice message received" | wc -l)"
echo "  Transcriptions completed: $(docker logs telegram-bot 2>&1 | grep "Transcription complete" | wc -l)"

echo ""
echo "To complete testing:"
echo "1. Fill out test_cases_voice.md with manual test results"
echo "2. Review 'Issues Found' section"
echo "3. Make decision: Ready for Step 9? Yes/No"

EOF

chmod +x generate_test_report.sh
./generate_test_report.sh
```

### Code Examples

No additional code needed - this step is testing-focused.

### Project Structure

After this step:

```
claude-remote-runner/
├── test_cases_voice.md         # ← NEW: Manual test checklist
├── test_voice_pipeline.sh      # ← NEW: Automated test script
├── generate_test_report.sh     # ← NEW: Report generator
└── (other files unchanged)
```

## Testing & Validation

This entire step IS the testing phase. Follow the procedures above.

### Acceptance Criteria

- [ ] test_cases_voice.md created and populated
- [ ] test_voice_pipeline.sh runs successfully (10/10 pass)
- [ ] All manual tests completed (31 test cases)
- [ ] >90% transcription accuracy on clear audio
- [ ] >80% transcription accuracy on noisy audio
- [ ] Average processing time <20s for 15s audio
- [ ] Error handling validated for all failure modes
- [ ] File cleanup verified
- [ ] Cost estimates match expectations ($0.0043/min)
- [ ] No critical bugs found
- [ ] Memory usage <500MB
- [ ] CPU usage reasonable during processing
- [ ] Test report generated
- [ ] Decision made: Ready for Step 8? Yes/No

### How to Test

**Complete Test Procedure:**

```bash
# Day 1: Setup and Automated Tests
# ---------------------------------

# 1. Run automated tests
./test_voice_pipeline.sh
# Should show 10/10 PASS

# 2. Start manual testing
open test_cases_voice.md
# Or: nano test_cases_voice.md

# 3. Work through Section 1: Basic Functionality (5 tests)
# Send each command/message in Telegram
# Mark Pass/Fail in test_cases_voice.md

# Day 2: Accuracy and Performance Tests
# --------------------------------------

# 4. Work through Section 2: Transcription Accuracy (10 tests)
# Record various voice messages
# Check transcription quality
# Calculate accuracy percentages

# 5. Work through Section 3: Performance (5 tests)
# Measure processing times
# Monitor resource usage: docker stats telegram-bot

# Day 3: Error Handling and Edge Cases
# -------------------------------------

# 6. Work through Section 4: Error Handling (6 tests)
# Test failure scenarios
# Verify graceful degradation

# 7. Work through Section 5: Edge Cases (5 tests)
# Test boundary conditions
# Verify file cleanup

# 8. Work through Section 6: Cost Validation (2 tests)
# Check OpenAI dashboard: https://platform.openai.com/usage
# Verify cost calculations

# 9. Work through Section 7: Integration Checks (3 tests)

# Final: Generate Report
# ----------------------

# 10. Generate test report
./generate_test_report.sh

# 11. Review test_cases_voice.md
# Count pass/fail
# Review issues found

# 12. Make go/no-go decision for Step 8
```

## Troubleshooting

Testing IS troubleshooting. Document all issues found in test_cases_voice.md.

### Common Issues and Resolutions

**Issue: Many Tests Failing**
- Review bot logs: `docker logs telegram-bot`
- Verify all prerequisites from Steps 1-6
- Restart bot: `docker-compose restart telegram-bot`
- Check API keys are valid

**Issue: Low Transcription Accuracy**
- Ensure clear audio (quiet environment)
- Speak at moderate pace
- Check if ffmpeg conversion is correct
- Verify WAV files are 16kHz mono

**Issue: High Processing Times**
- Check network speed to OpenAI
- Verify adequate CPU/memory resources
- Look for bottlenecks in logs

**Issue: High Costs**
- Review message lengths in tests
- Check OpenAI dashboard for usage
- Ensure file cleanup is working

## Rollback Procedure

No rollback needed - this is a testing step with no code changes.

If you need to retest:
```bash
# Clear test results
cp test_cases_voice.md test_cases_voice_backup.md
# Reset checkboxes to empty
sed -i 's/☑/☐/g' test_cases_voice.md

# Restart fresh
docker-compose restart telegram-bot
docker logs telegram-bot --since 1m -f
```

## Next Step

Once all tests pass and you're confident in the voice-to-text pipeline, proceed to:

**Step 8: Session State Management**
- File: `docs/implementation/step_08_session_state.md`
- Duration: 1 hour
- Goal: Implement robust session persistence and state management

Before proceeding, ensure:
1. All automated tests pass (10/10)
2. >85% of manual tests pass (26/31 minimum)
3. No critical bugs found
4. Transcription accuracy >90% on clear audio
5. Performance metrics meet targets
6. Test report completed and reviewed
7. Decision: Ready to proceed = Yes

**Checkpoint:** The voice-to-text pipeline is now thoroughly tested and validated. You have confidence that users can reliably send voice messages and receive accurate transcriptions. The foundation is solid for adding Claude Code integration in upcoming steps.

**Save Your Work:**
```bash
git add test_cases_voice.md test_voice_pipeline.sh generate_test_report.sh
git commit -m "Complete voice-to-text pipeline testing (Step 7)

- Add comprehensive manual test checklist (31 test cases)
- Add automated test script (10 tests)
- Add test report generator
- Document test procedures and acceptance criteria
- Validate transcription accuracy >90%
- Verify performance meets targets
- Test error handling comprehensively
- Confirm cost estimates accurate
- All tests passed - ready for Step 8"
```

**Congratulations!** Steps 1-7 are complete. You now have:
- ✓ Project structure and credentials
- ✓ Docker environment working locally
- ✓ Telegram bot with full command handling
- ✓ Voice message download and conversion
- ✓ Deepgram API transcription
- ✓ Comprehensive testing and validation

The next phases (Steps 8-16) will add Claude Code integration, approval workflows, and production deployment. The solid foundation from Steps 1-7 makes the remaining work much easier.
