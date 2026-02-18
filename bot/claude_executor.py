#!/usr/bin/env python3
"""
Claude Code execution module for headless operation.
Handles subprocess execution, output parsing, and error handling.
"""

import subprocess
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable, Awaitable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Claude Code executable path
CLAUDE_EXECUTABLE = "claude"

# Default workspace directory
DEFAULT_WORKSPACE = Path("/workspace")

# Command timeout in seconds
DEFAULT_TIMEOUT = 3600  # 1 hour - complex tasks (multi-file projects) can take a long time

# Claude session directory
CLAUDE_SESSIONS_DIR = Path("/root/.claude/projects")


@dataclass
class ClaudeResponse:
    """Structured response from Claude Code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    session_id: Optional[str] = None
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    model: Optional[str] = None
    tools_used: List[str] = field(default_factory=list)
    raw_events: List[Dict[str, Any]] = field(default_factory=list)


class ClaudeExecutor:
    """Execute Claude Code commands and parse output."""

    def __init__(
        self,
        workspace: Path = DEFAULT_WORKSPACE,
        timeout: int = DEFAULT_TIMEOUT,
        max_turns: int = 10
    ):
        self.workspace = workspace
        self.timeout = timeout
        self.max_turns = max_turns

    def execute(
        self,
        prompt: str,
        session_id: Optional[str] = None
    ) -> ClaudeResponse:
        """
        Execute a Claude Code command.

        Args:
            prompt: The user's prompt/request
            session_id: Optional session ID to resume conversation

        Returns:
            ClaudeResponse object with execution results
        """
        # Build command
        cmd = self._build_command(prompt, session_id)

        logger.info(f"Executing Claude command for session: {session_id or 'new'}")
        logger.debug(f"Command: {' '.join(cmd[:5])}...")

        try:
            # Execute with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.workspace),
                timeout=self.timeout
            )

            # Parse stream-json output
            return self._parse_stream_json(result)

        except subprocess.TimeoutExpired as e:
            logger.error(f"Claude command timeout after {self.timeout}s")
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Command timeout after {self.timeout} seconds"
            )

        except Exception as e:
            logger.error(f"Claude execution failed: {e}", exc_info=True)
            return ClaudeResponse(
                success=False,
                output="",
                error=f"Execution error: {str(e)}"
            )

    def _build_command(
        self,
        prompt: str,
        session_id: Optional[str]
    ) -> List[str]:
        """Build the Claude Code command with all arguments."""
        cmd = [
            CLAUDE_EXECUTABLE,
            "-p", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--max-turns", str(self.max_turns)
        ]

        # Add session resumption if provided
        if session_id:
            cmd.extend(["--resume", session_id])

        return cmd

    def _parse_stream_json(self, result: subprocess.CompletedProcess) -> ClaudeResponse:
        """Parse streaming JSON output from Claude Code."""
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else None

            # Try to extract error from JSON stdout
            if not error_msg and result.stdout:
                try:
                    # Parse last line which usually contains error
                    lines = result.stdout.strip().split('\n')
                    for line in reversed(lines):
                        if line.strip():
                            event = json.loads(line)
                            if event.get('type') == 'result' and event.get('subtype') == 'error_during_execution':
                                errors = event.get('errors', [])
                                if errors:
                                    error_msg = errors[0]
                                    break
                except (json.JSONDecodeError, KeyError, IndexError):
                    pass

            if not error_msg:
                error_msg = "Unknown error"

            logger.error(f"Claude returned error (code {result.returncode}): {error_msg}")
            return ClaudeResponse(
                success=False,
                output="",
                error=error_msg
            )

        # Parse line-by-line JSON events
        events = []
        output_parts = []
        session_id = None
        cost_usd = 0.0
        input_tokens = 0
        output_tokens = 0
        duration_ms = 0
        model = None
        tools_used = set()

        for line in result.stdout.strip().split('\n'):
            if not line.strip():
                continue

            try:
                event = json.loads(line)
                events.append(event)

                event_type = event.get('type')

                # Extract session ID from system init
                if event_type == 'system' and event.get('subtype') == 'init':
                    session_id = event.get('session_id')
                    model = event.get('model')
                    logger.debug(f"Session initialized: {session_id}, model: {model}")

                # Extract text content from assistant messages
                elif event_type == 'assistant':
                    message = event.get('message', {})
                    content = message.get('content', [])
                    for block in content:
                        if block.get('type') == 'text':
                            output_parts.append(block.get('text', ''))
                        elif block.get('type') == 'tool_use':
                            tool_name = block.get('name', 'unknown')
                            tools_used.add(tool_name)

                # Extract final result with cost and tokens
                elif event_type == 'result':
                    if not session_id:  # Fallback if not in system event
                        session_id = event.get('session_id')
                    cost_usd = event.get('total_cost_usd', 0.0)
                    duration_ms = event.get('duration_ms', 0)

                    usage = event.get('usage', {})
                    input_tokens = usage.get('input_tokens', 0)
                    output_tokens = usage.get('output_tokens', 0)

            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON line: {line[:100]}")
                continue

        output = ''.join(output_parts).strip()

        # Check if execution was successful
        is_success = result.returncode == 0 and (output or tools_used)

        # Set placeholder message if no text output
        if not output and tools_used:
            output = "(Claude completed task with no text output)"

        return ClaudeResponse(
            success=is_success,
            output=output,
            session_id=session_id,
            cost_usd=cost_usd,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            model=model,
            tools_used=list(tools_used),
            raw_events=events
        )

    async def execute_streaming(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        on_progress: Optional[Callable[[str], Awaitable[None]]] = None
    ) -> ClaudeResponse:
        """
        Execute Claude Code asynchronously with streaming progress updates.

        Args:
            prompt: The user's prompt/request
            session_id: Optional session ID to resume conversation
            on_progress: Async callback called with progress text as events arrive

        Returns:
            ClaudeResponse object with execution results
        """
        cmd = self._build_command(prompt, session_id)
        logger.info(f"Executing Claude (streaming) for session: {session_id or 'new'}")

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace)
        )

        events = []
        output_parts = []
        result_session_id = None
        cost_usd = 0.0
        input_tokens = 0
        output_tokens = 0
        duration_ms = 0
        model = None
        tools_used = set()
        last_progress_time = asyncio.get_event_loop().time()
        tool_call_count = 0

        try:
            async def read_stdout():
                nonlocal result_session_id, cost_usd, input_tokens, output_tokens
                nonlocal duration_ms, model, last_progress_time, tool_call_count

                async for raw_line in proc.stdout:
                    line = raw_line.decode('utf-8', errors='replace').strip()
                    if not line:
                        continue

                    try:
                        event = json.loads(line)
                        events.append(event)
                        event_type = event.get('type')

                        if event_type == 'system' and event.get('subtype') == 'init':
                            result_session_id = event.get('session_id')
                            model = event.get('model')

                        elif event_type == 'assistant':
                            message = event.get('message', {})
                            content = message.get('content', [])
                            for block in content:
                                if block.get('type') == 'text':
                                    output_parts.append(block.get('text', ''))
                                elif block.get('type') == 'tool_use':
                                    tool_name = block.get('name', 'unknown')
                                    tools_used.add(tool_name)
                                    tool_call_count += 1
                                    # Send progress update for each tool call
                                    if on_progress:
                                        now = asyncio.get_event_loop().time()
                                        elapsed = int(now - last_progress_time + 0.5)
                                        # Build tool display name
                                        tool_input = block.get('input', {})
                                        detail = ''
                                        if tool_name in ('Write', 'Edit', 'Create') and 'file_path' in tool_input:
                                            detail = f": `{tool_input['file_path'].split('/')[-1]}`"
                                        elif tool_name == 'Bash' and 'command' in tool_input:
                                            detail = f": `{tool_input['command'][:40]}`"
                                        elif tool_name == 'Read' and 'file_path' in tool_input:
                                            detail = f": `{tool_input['file_path'].split('/')[-1]}`"
                                        await on_progress(
                                            f"🔧 `{tool_name}`{detail} (step {tool_call_count})"
                                        )

                        elif event_type == 'result':
                            if not result_session_id:
                                result_session_id = event.get('session_id')
                            cost_usd = event.get('total_cost_usd', 0.0)
                            duration_ms = event.get('duration_ms', 0)
                            usage = event.get('usage', {})
                            input_tokens = usage.get('input_tokens', 0)
                            output_tokens = usage.get('output_tokens', 0)

                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON line: {line[:100]}")

            await asyncio.wait_for(read_stdout(), timeout=self.timeout)
            await proc.wait()

        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            logger.error(f"Claude streaming command timeout after {self.timeout}s")
            return ClaudeResponse(
                success=False,
                output=''.join(output_parts).strip(),
                error=f"Command timeout after {self.timeout} seconds"
            )

        output = ''.join(output_parts).strip()
        is_success = proc.returncode == 0 and (output or tools_used)

        if not output and tools_used:
            output = "(Claude completed task with no text output)"

        if proc.returncode != 0 and not output:
            stderr = (await proc.stderr.read()).decode('utf-8', errors='replace').strip()
            return ClaudeResponse(
                success=False,
                output="",
                error=stderr or "Unknown error"
            )

        return ClaudeResponse(
            success=is_success,
            output=output,
            session_id=result_session_id,
            cost_usd=cost_usd,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            duration_ms=duration_ms,
            model=model,
            tools_used=list(tools_used),
            raw_events=events
        )

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific session.

        Args:
            session_id: The session ID to query

        Returns:
            Dictionary with session info or None if not found
        """
        session_dir = CLAUDE_SESSIONS_DIR / session_id

        if not session_dir.exists():
            return None

        try:
            stat = session_dir.stat()

            # Count files in session directory
            file_count = sum(1 for f in session_dir.rglob('*') if f.is_file())

            return {
                'session_id': session_id,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'size_bytes': sum(f.stat().st_size for f in session_dir.rglob('*') if f.is_file()),
                'file_count': file_count,
                'exists': True
            }

        except Exception as e:
            logger.error(f"Failed to get session info for {session_id}: {e}")
            return None

    def list_sessions(self, user_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all available Claude sessions.

        Args:
            user_filter: Optional filter to match session IDs (e.g., "user_123")

        Returns:
            List of session info dictionaries
        """
        try:
            if not CLAUDE_SESSIONS_DIR.exists():
                logger.warning(f"Claude sessions directory does not exist: {CLAUDE_SESSIONS_DIR}")
                return []

            sessions = []

            for session_dir in CLAUDE_SESSIONS_DIR.iterdir():
                if not session_dir.is_dir():
                    continue

                session_id = session_dir.name

                # Apply filter if provided
                if user_filter and not session_id.startswith(user_filter):
                    continue

                info = self.get_session_info(session_id)
                if info:
                    sessions.append(info)

            # Sort by most recently modified
            sessions.sort(key=lambda s: s['modified'], reverse=True)

            return sessions

        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a Claude session.

        Args:
            session_id: The session ID to delete

        Returns:
            True if successful, False otherwise
        """
        session_dir = CLAUDE_SESSIONS_DIR / session_id

        if not session_dir.exists():
            logger.warning(f"Session {session_id} not found")
            return False

        try:
            import shutil
            shutil.rmtree(session_dir)
            logger.info(f"Deleted session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    def cleanup_old_sessions(
        self,
        user_filter: Optional[str] = None,
        max_age_days: int = 30
    ) -> int:
        """
        Delete sessions older than max_age_days.

        Args:
            user_filter: Optional filter for session IDs
            max_age_days: Maximum age in days before deletion

        Returns:
            Number of sessions deleted
        """
        import time

        cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
        deleted_count = 0

        sessions = self.list_sessions(user_filter=user_filter)

        for session in sessions:
            if session['modified'] < cutoff_time:
                if self.delete_session(session['session_id']):
                    deleted_count += 1

        logger.info(f"Cleaned up {deleted_count} old sessions (older than {max_age_days} days)")
        return deleted_count
