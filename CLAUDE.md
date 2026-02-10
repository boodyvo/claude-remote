# Claude Code Instructions for claude-remote-runner

## Project Overview

This is the **claude-remote-runner** project - a system for running Claude Code remotely with voice control via Telegram bot, deployed on Coolify/Hetzner.

**Current Status:** Planning & Documentation Complete → Ready for Implementation
**Your Role:** Help implement all 28 steps according to detailed implementation plan

## CRITICAL RULES

### Testing & Validation Rule
**NEVER commit code without testing and validation first!**

1. **Before any commit:**
   - Write automated tests for new functionality
   - Run all tests and verify they pass
   - Manually test if automated testing is not possible
   - Validate the functionality works as expected

2. **Test-first approach:**
   - Create tests before or alongside implementation
   - No code goes to repository without proof it works
   - If tests fail, fix the code before committing

3. **Validation requirements:**
   - Automated tests: 100% pass rate required
   - Manual tests: Document steps and results
   - Integration: Test with actual services (Telegram, Deepgram, Claude)

**This rule applies to ALL commits, no exceptions!**

## Project Context

### What We're Building
- Remote Claude Code server with persistent sessions
- Voice control via Telegram bot + OpenAI Whisper transcription
- Web UI for terminal access (koogle/claudebox)
- Interactive approval workflow with inline keyboards
- Git integration for code review
- Production deployment on existing Coolify/Hetzner infrastructure

### Technology Stack
- **Platform:** Coolify (already installed) on Hetzner CPX21 VPS
- **Containerization:** Docker Compose
- **Bot Framework:** python-telegram-bot v21.9
- **STT:** OpenAI Whisper API
- **Claude Integration:** Anthropic Claude API (headless mode)
- **Web Terminal:** koogle/claudebox (xterm.js + WebSocket)

### Budget
- **Monthly Cost:** $66-96 (€9 VPS + $36 Whisper + $20-50 Claude API)
- **Time Estimate:** 16-20 hours total implementation

## Documentation Structure

All project documentation is in `docs/`:

### Core Planning Documents
1. **`docs/implementation_plan.md`** - Master plan with 7 phases, 28 steps, timelines
2. **`docs/design.md`** - Complete system architecture and design
3. **`docs/comprehensive_research.md`** - Technology research and comparisons

### Implementation Guides (28 Steps)
All in **`docs/implementation/`** directory:
- Each step is a separate markdown file: `step_XX_name.md`
- Follow steps **sequentially** from 01 to 28
- Each step has: Overview, Implementation, Testing, Acceptance Criteria, Troubleshooting, Rollback

### Progress Tracking
- **`docs/implementation/README.md`** - Quick reference with checkboxes for all 28 steps
- **`CONTEXT.md`** - Current state, progress, blockers, decisions (update frequently)

## Implementation Phases

### Phase 1: Foundation & Setup (Steps 1-4) - 3-4 hours
**Goal:** Local development environment + basic bot

**Steps:**
1. Project setup & Git initialization (30 min)
2. Obtain API keys (Telegram, Anthropic, OpenAI) (30 min)
3. Local Docker Compose testing (1-2 hours)
4. Telegram bot foundation (1 hour)

**Deliverable:** Bot responds to `/start` command locally

### Phase 2: Voice Processing Pipeline (Steps 5-8) - 3-4 hours
**Goal:** Voice transcription working end-to-end

**Steps:**
5. Voice message download & OGG→WAV conversion (1 hour)
6. Whisper API integration (1 hour)
7. Echo bot testing (30 min)
8. Session state management with persistence (1 hour)

**Deliverable:** Bot transcribes voice and echoes back text

### Phase 3: Claude Code Integration (Steps 9-12) - 3-4 hours
**Goal:** Execute voice commands via Claude Code

**Steps:**
9. Claude Code headless execution (1-2 hours)
10. Session ID management (1 hour)
11. Response formatting for Telegram (30 min)
12. Error handling & logging (30 min)

**Deliverable:** Voice command → Claude executes → returns results

### Phase 4: Interactive UI & Approvals (Steps 13-16) - 2-3 hours
**Goal:** Approval workflow with git integration

**Steps:**
13. Inline keyboard implementation (1 hour)
14. Git integration (diff, status, commit) (1 hour)
15. Approval workflow (30 min)
16. Command helpers (/status, /clear, /help) (30 min)

**Deliverable:** Interactive bot with approval buttons and git commands

### Phase 5: Production Deployment (Steps 17-20) - 2-3 hours
**Goal:** Live on Coolify with HTTPS

**Steps:**
17. Git repository preparation (30 min)
18. Coolify deployment configuration (1 hour)
19. Production deployment (30 min)
20. Webhook configuration (30 min)

**Deliverable:** Production system at https://claude.yourdomain.com

### Phase 6: Monitoring, Backup & Optimization (Steps 21-24) - 2-3 hours
**Goal:** Production hardening

**Steps:**
21. Monitoring setup (1 hour)
22. Backup implementation (1 hour)
23. Performance optimization (30 min)
24. Security hardening (30 min)

**Deliverable:** Production-ready system with monitoring and backups

### Phase 7: Documentation & Handoff (Steps 25-28) - 1-2 hours
**Goal:** Complete documentation

**Steps:**
25. User documentation (30 min)
26. Operational runbooks (30 min)
27. Cost analysis & optimization guide (30 min)
28. Final testing & acceptance (30 min)

**Deliverable:** Full documentation package and validated system

## Current Implementation State

**See `CONTEXT.md` for:**
- Current step in progress
- Completed steps
- Blockers or issues
- Recent decisions
- Next actions

**Update `CONTEXT.md` after each step completion!**

## Working with Claude Code

### Repository Hygiene - IMPORTANT

**Keep the repository clean and minimal:**

1. **Remove temporary/validation scripts after use**
   - Delete validation scripts once step is validated and committed
   - Remove test files, temporary scripts, debugging code
   - Clean up before each commit

2. **Keep documentation compact**
   - CONTEXT.md: Keep only last 2-3 activity entries, archive old ones
   - Remove outdated information that no longer applies
   - Be concise - facts only, no redundant explanations

3. **What to keep vs remove:**
   - ✅ Keep: Source code, configs, essential docs, .gitkeep files
   - ❌ Remove: Validation scripts after validation, temp files, old notes
   - ❌ Remove: Completed step documentation references once internalized

4. **Update, don't accumulate:**
   - Update existing sections rather than adding new ones
   - Replace outdated info rather than appending corrections
   - Merge related decisions rather than creating duplicates

### When Starting a Session

1. **Read CONTEXT.md first** to understand current state
2. **Check implementation plan** in `docs/implementation_plan.md`
3. **Follow current step** from `docs/implementation/step_XX_*.md`
4. **Update CONTEXT.md** with progress (keep compact!)
5. **Clean up** temporary files from previous step before committing

### When Implementing a Step

1. **Read the full step document** before starting
2. **Check prerequisites** are met
3. **Follow implementation details** exactly
4. **Run all test procedures** from the step document
5. **Validate acceptance criteria** before marking complete
6. **Update CONTEXT.md** with:
   - What was completed
   - Any deviations from plan
   - Blockers encountered
   - Decisions made

### Code Quality Standards

- **Python:** Follow PEP 8, use type hints, comprehensive docstrings
- **Docker:** Multi-stage builds, minimal layers, security best practices
- **Configuration:** Use environment variables, never commit secrets
- **Testing:** Test each component before integration
- **Documentation:** Update docs as you implement

### File Organization

Expected final structure:
```
claude-remote-runner/
├── CLAUDE.md                    # This file - Claude's instructions
├── CONTEXT.md                   # Current state and progress
├── README.md                    # Project overview
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignore rules
├── .env.example                 # Template for environment variables
├── docker-compose.yml           # Main Docker Compose configuration
├── bot/                         # Telegram bot code
│   ├── bot.py                   # Main bot application
│   ├── requirements.txt         # Python dependencies
│   ├── config.py                # Configuration management
│   ├── handlers/                # Message handlers
│   ├── keyboards.py             # Inline keyboard layouts
│   └── utils/                   # Utility modules
├── workspace/                   # Mounted as /workspace in containers
├── sessions/                    # Bot session persistence (created at runtime)
├── backups/                     # Backup storage (created at runtime)
└── docs/                        # All documentation
    ├── implementation_plan.md
    ├── design.md
    ├── comprehensive_research.md
    └── implementation/
        ├── README.md
        └── step_01_project_setup.md through step_28_final_testing.md
```

## Important Constraints

### What We Already Have
- ✅ **Coolify installed** on Hetzner server (don't reinstall)
- ✅ **SSH access** to server
- ✅ **Multiple projects running** in production on same Coolify
- ✅ **Domain available** for this project

### What We Need to Obtain
- [ ] Telegram bot token (Step 2)
- [ ] Anthropic API key (Step 2)
- [ ] OpenAI API key (Step 2)

### Critical Configuration Notes

**For Coolify Deployment:**
- ❌ **Do NOT use `ports:` section** in docker-compose.yml (Coolify manages this via Traefik)
- ✅ **Do use environment variables with `:?`** to mark required vars
- ✅ **Do use named volumes** for persistence
- ✅ Set "Ports Exposed" in Coolify UI, not in compose file
- ✅ Use `https://` prefix for domains to enable SSL

**For Security:**
- Never commit `.env` file to Git
- Store all secrets in Coolify environment variables UI
- Mark sensitive variables as "Secret" in Coolify
- Use user ID allowlist for Telegram bot access

**For Docker:**
- Use specific version tags, not `latest`
- Include health checks for all services
- Use multi-stage builds where applicable
- Minimize image sizes

## Testing Strategy

### Unit Testing
Test individual functions in isolation before integration.

### Integration Testing
Test component interactions (voice → transcription → Claude → response).

### System Testing
Test entire deployed system end-to-end.

### Acceptance Testing
Validate against acceptance criteria in each step document.

**Test early and often!** Each step has specific test procedures.

## Troubleshooting

If you encounter issues:

1. **Check step's Troubleshooting section** in the step document
2. **Review CONTEXT.md** for recent changes that might have caused issue
3. **Check logs:**
   - Docker: `docker compose logs <service>`
   - Coolify: Use web UI → Application → Logs
4. **Verify environment variables** are set correctly
5. **Check acceptance criteria** to see what might be missing
6. **Use rollback procedure** from step document if needed

## Common Pitfalls to Avoid

- ❌ Skipping test procedures (test at every step!)
- ❌ Not updating CONTEXT.md (will lose track of progress)
- ❌ Moving to next step before acceptance criteria met
- ❌ Committing secrets to Git
- ❌ Using `ports:` in docker-compose.yml for Coolify
- ❌ Forgetting to mark env vars as required (`:?`)
- ❌ Not reading full step document before starting

## Success Criteria

Project is complete when:
- ✅ All 28 steps have passing acceptance criteria
- ✅ Voice message in Telegram → transcribed → executed by Claude → results returned
- ✅ Approve/reject buttons work
- ✅ Git diff/status work
- ✅ Session context persists across messages
- ✅ System running on Coolify with HTTPS
- ✅ Backups configured and tested
- ✅ Monitoring operational
- ✅ Security hardened (user auth, rate limiting)
- ✅ Documentation complete

## Cost Tracking

Monitor costs throughout implementation:
- **OpenAI:** Check https://platform.openai.com/usage for Whisper API
- **Anthropic:** Check https://console.anthropic.com/ for Claude API
- **Hetzner:** Fixed €9/month for CPX21 VPS
- **Target:** Stay within $66-96/month budget

## Communication Style

When working on this project:
- **Be concise** - focus on implementation, not explanations
- **Test early** - validate each component before integration
- **Update CONTEXT.md** - keep state current
- **Follow the plan** - stick to implementation guides unless there's a good reason to deviate
- **Document deviations** - if you change approach, explain why in CONTEXT.md

## Emergency Procedures

### If Deployment Fails
1. Check Coolify logs immediately
2. Use rollback procedure from step document
3. Restore from backup if needed (Step 22 procedures)
4. Document failure in CONTEXT.md
5. Analyze root cause before retrying

### If Cost Exceeds Budget
1. Stop all API-consuming services
2. Check OpenAI and Anthropic dashboards for usage
3. Review CONTEXT.md for what triggered high usage
4. Implement rate limiting (Step 23)
5. Consider cheaper alternatives (AssemblyAI for STT)

### If Security Incident
1. Immediately rotate all API keys
2. Check Coolify logs for unauthorized access
3. Review user allowlist
4. Enable additional security measures (Fail2ban, etc.)
5. Document incident and response in CONTEXT.md

## Resources

### Internal Documentation
- **Implementation Plan:** `docs/implementation_plan.md`
- **Design Document:** `docs/design.md`
- **Research:** `docs/comprehensive_research.md`
- **Step Guides:** `docs/implementation/step_XX_*.md`
- **Progress Tracking:** `docs/implementation/README.md`
- **Current State:** `CONTEXT.md`

### External Resources
- **Coolify Docs:** https://coolify.io/docs/
- **Telegram Bot API:** https://core.telegram.org/bots/api
- **python-telegram-bot:** https://docs.python-telegram-bot.org/
- **OpenAI Whisper:** https://platform.openai.com/docs/guides/speech-to-text
- **Claude Code:** https://code.claude.com/docs/

### Community
- **Coolify Discord:** https://discord.gg/coolify
- **Telegram Bot Developers:** https://t.me/BotDevelopment

## Version History

- **v1.0** (2026-02-04): Initial documentation package complete, ready for implementation

## Next Steps

**To begin implementation:**
1. Read this CLAUDE.md file (you're doing it now!)
2. Read CONTEXT.md to understand current state
3. Start with `docs/implementation/step_01_project_setup.md`
4. Update CONTEXT.md after completing each step

---

**Remember:** This is a well-planned project with detailed documentation for every step. Trust the process, follow the guides, test thoroughly, and update CONTEXT.md frequently. You've got this! 🚀
