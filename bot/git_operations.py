#!/usr/bin/env python3
"""
Git operations module for the Telegram bot.
Provides safe wrappers around git commands.
"""

import subprocess
import logging
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GitStatus:
    """Git repository status."""
    is_repo: bool
    is_clean: bool
    branch: str
    staged: List[str]
    modified: List[str]
    untracked: List[str]
    ahead: int = 0
    behind: int = 0


@dataclass
class GitDiff:
    """Git diff result."""
    has_changes: bool
    diff_output: str
    files_changed: List[str]
    insertions: int = 0
    deletions: int = 0


class GitOperations:
    """Git operations wrapper with error handling."""

    def __init__(self, workspace: Path = Path('/workspace')):
        self.workspace = workspace

    def _run_git(
        self,
        args: List[str],
        timeout: int = 30,
        check: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run a git command.

        Args:
            args: Git command arguments (without 'git' prefix)
            timeout: Command timeout in seconds
            check: Whether to raise on non-zero exit code

        Returns:
            CompletedProcess result
        """
        cmd = ['git'] + args

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(self.workspace),
                timeout=timeout,
                check=check
            )
            return result

        except subprocess.TimeoutExpired as e:
            logger.error(f"Git command timeout: {' '.join(cmd)}")
            raise

        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr}")
            raise

        except Exception as e:
            logger.error(f"Git command error: {e}")
            raise

    def is_git_repo(self) -> bool:
        """Check if workspace is a git repository."""
        try:
            result = self._run_git(['rev-parse', '--git-dir'])
            return result.returncode == 0
        except Exception:
            return False

    def init_repo(self) -> Tuple[bool, str]:
        """
        Initialize a new git repository.

        Returns:
            Tuple of (success, message)
        """
        try:
            if self.is_git_repo():
                return (False, "Repository already initialized")

            self._run_git(['init'])
            self._run_git(['config', 'user.name', 'Claude Bot'])
            self._run_git(['config', 'user.email', 'bot@claude.local'])

            logger.info(f"Initialized git repo in {self.workspace}")
            return (True, "Git repository initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize repo: {e}")
            return (False, f"Failed to initialize: {str(e)}")

    def get_status(self) -> Optional[GitStatus]:
        """
        Get repository status.

        Returns:
            GitStatus object or None if not a git repo
        """
        if not self.is_git_repo():
            return None

        try:
            # Get current branch
            branch_result = self._run_git(['branch', '--show-current'])
            branch = branch_result.stdout.strip() or 'HEAD'

            # Get status in porcelain format
            status_result = self._run_git(['status', '--porcelain=v1', '--branch'])
            status_lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

            staged = []
            modified = []
            untracked = []
            ahead = 0
            behind = 0

            for line in status_lines:
                if line.startswith('##'):
                    # Branch line with ahead/behind info
                    if '[ahead ' in line:
                        ahead = int(line.split('[ahead ')[1].split(']')[0].split(',')[0])
                    if 'behind ' in line:
                        behind = int(line.split('behind ')[1].split(']')[0])
                    continue

                if len(line) < 3:
                    continue

                status_code = line[:2]
                filename = line[3:]

                # Parse status codes
                if status_code[0] != ' ':
                    staged.append(filename)
                if status_code[1] == 'M':
                    modified.append(filename)
                elif status_code == '??':
                    untracked.append(filename)

            is_clean = not (staged or modified or untracked)

            return GitStatus(
                is_repo=True,
                is_clean=is_clean,
                branch=branch,
                staged=staged,
                modified=modified,
                untracked=untracked,
                ahead=ahead,
                behind=behind
            )

        except Exception as e:
            logger.error(f"Failed to get git status: {e}")
            return None

    def get_diff(
        self,
        staged: bool = False,
        unified: int = 3
    ) -> Optional[GitDiff]:
        """
        Get diff of changes.

        Args:
            staged: Show staged changes instead of unstaged
            unified: Number of context lines

        Returns:
            GitDiff object or None if error
        """
        if not self.is_git_repo():
            return None

        try:
            args = ['diff', f'--unified={unified}']
            if staged:
                args.append('--staged')

            result = self._run_git(args)
            diff_output = result.stdout

            # Parse diff for stats
            stat_result = self._run_git(['diff', '--stat'] + (['--staged'] if staged else []))
            stat_output = stat_result.stdout

            # Extract file list
            files_changed = []
            insertions = 0
            deletions = 0

            if stat_output:
                lines = stat_output.strip().split('\n')
                for line in lines[:-1]:  # Last line is summary
                    if '|' in line:
                        filename = line.split('|')[0].strip()
                        files_changed.append(filename)

                # Parse summary line
                if lines:
                    summary = lines[-1]
                    if 'insertion' in summary:
                        parts = summary.split('insertion')[0].split(',')
                        if parts:
                            insertions = int(parts[-1].strip())
                    if 'deletion' in summary:
                        parts = summary.split('deletion')[0].split(',')
                        if parts:
                            deletions = int(parts[-1].strip())

            return GitDiff(
                has_changes=bool(diff_output),
                diff_output=diff_output,
                files_changed=files_changed,
                insertions=insertions,
                deletions=deletions
            )

        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            return None

    def add_files(self, files: Optional[List[str]] = None) -> Tuple[bool, str]:
        """
        Stage files for commit.

        Args:
            files: List of files to stage, or None for all

        Returns:
            Tuple of (success, message)
        """
        if not self.is_git_repo():
            return (False, "Not a git repository")

        try:
            if files is None or files == ['.']:
                # Add all files
                self._run_git(['add', '-A'])
                message = "All changes staged"
            else:
                # Add specific files
                self._run_git(['add'] + files)
                message = f"Staged {len(files)} file(s)"

            logger.info(f"Staged files: {files or 'all'}")
            return (True, message)

        except Exception as e:
            logger.error(f"Failed to stage files: {e}")
            return (False, f"Failed to stage: {str(e)}")

    def commit(
        self,
        message: str,
        amend: bool = False
    ) -> Tuple[bool, str]:
        """
        Create a commit.

        Args:
            message: Commit message
            amend: Amend previous commit

        Returns:
            Tuple of (success, message/commit_hash)
        """
        if not self.is_git_repo():
            return (False, "Not a git repository")

        if not message.strip():
            return (False, "Commit message cannot be empty")

        try:
            args = ['commit', '-m', message]
            if amend:
                args.append('--amend')

            result = self._run_git(args)

            # Extract commit hash
            hash_result = self._run_git(['rev-parse', '--short', 'HEAD'])
            commit_hash = hash_result.stdout.strip()

            logger.info(f"Created commit {commit_hash}: {message[:50]}")
            return (True, commit_hash)

        except subprocess.CalledProcessError as e:
            error = e.stderr.strip()
            if "nothing to commit" in error:
                return (False, "No changes to commit")
            return (False, f"Commit failed: {error}")

        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            return (False, f"Failed to commit: {str(e)}")

    def get_log(self, count: int = 10) -> List[dict]:
        """
        Get commit history.

        Args:
            count: Number of commits to retrieve

        Returns:
            List of commit dictionaries
        """
        if not self.is_git_repo():
            return []

        try:
            # Format: hash|author|date|message
            format_str = '%h|%an|%ar|%s'
            result = self._run_git([
                'log',
                f'-{count}',
                f'--pretty=format:{format_str}'
            ])

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|', 3)
                if len(parts) == 4:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'date': parts[2],
                        'message': parts[3]
                    })

            return commits

        except Exception as e:
            logger.error(f"Failed to get log: {e}")
            return []

    def get_branches(self) -> List[str]:
        """Get list of branches."""
        if not self.is_git_repo():
            return []

        try:
            result = self._run_git(['branch', '-a'])
            branches = [
                line.strip().replace('* ', '')
                for line in result.stdout.strip().split('\n')
                if line.strip()
            ]
            return branches

        except Exception as e:
            logger.error(f"Failed to get branches: {e}")
            return []

    def generate_commit_message(self) -> str:
        """
        Generate a commit message based on changes.

        Returns:
            Generated commit message
        """
        try:
            diff = self.get_diff()
            if not diff or not diff.has_changes:
                return "Update files"

            # Simple message based on changes
            files = diff.files_changed
            if len(files) == 1:
                return f"Update {files[0]}"
            elif len(files) <= 3:
                return f"Update {', '.join(files)}"
            else:
                return f"Update {len(files)} files"

        except Exception:
            return "Update files"
