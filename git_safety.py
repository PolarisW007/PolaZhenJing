"""Guarded git staging helpers for article publishing flows."""

from __future__ import annotations

import fnmatch
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ALLOWED_PATTERNS = (
    "_posts/*.md",
    "assets/images/**",
)

DENY_PATH_PATTERNS = (
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "*secret*",
    "*token*",
    "*cookie*",
    "*backup*",
    "*.bak",
    "*.db",
    "__pycache__/**",
    "**/__pycache__/**",
    ".qa-artifacts/**",
    "data/wiki.db",
)

SECRET_CONTENT_RE = re.compile(
    r"(AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|PRIVATE) KEY|"
    r"(api[_-]?key|access[_-]?token|secret|password|cookie)\s*[:=]\s*['\"]?[^'\"\s]{12,})",
    re.IGNORECASE,
)


@dataclass
class GitDeployResult:
    allowed: list[str]
    denied: list[str]
    committed: bool = False
    pushed: bool = False
    commit_message: str = ""
    stdout: str = ""
    stderr: str = ""


class GitSafetyError(RuntimeError):
    """Raised when unsafe files would be staged or committed."""


def _run_git(project_root: Path, args: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _matches(path: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _parse_porcelain(stdout: str) -> list[str]:
    files: list[str] = []
    for raw_line in stdout.splitlines():
        if not raw_line:
            continue
        path = raw_line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        files.append(path.strip())
    return files


def changed_files(project_root: str | Path) -> list[str]:
    root = Path(project_root)
    result = _run_git(root, ["status", "--porcelain", "--untracked-files=all"])
    if result.returncode != 0:
        raise GitSafetyError(result.stderr.strip() or "git status failed")
    return _parse_porcelain(result.stdout)


def split_stage_candidates(
    project_root: str | Path,
    *,
    allowed_patterns: tuple[str, ...] = DEFAULT_ALLOWED_PATTERNS,
) -> tuple[list[str], list[str]]:
    root = Path(project_root)
    allowed: list[str] = []
    denied: list[str] = []
    for rel_path in changed_files(root):
        normalized = rel_path.replace("\\", "/")
        if _matches(normalized, DENY_PATH_PATTERNS):
            denied.append(normalized)
            continue
        if not _matches(normalized, allowed_patterns):
            denied.append(normalized)
            continue
        if _contains_secret(root / normalized):
            denied.append(normalized)
            continue
        allowed.append(normalized)
    return sorted(set(allowed)), sorted(set(denied))


def _contains_secret(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        if path.stat().st_size > 1_000_000:
            return False
        content = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return True
    return bool(SECRET_CONTENT_RE.search(content))


def guarded_commit_and_push(
    project_root: str | Path,
    message: str,
    *,
    push: bool = True,
    push_args: list[str] | None = None,
    dry_run: bool = False,
) -> GitDeployResult:
    root = Path(project_root)
    allowed, denied = split_stage_candidates(root)
    if denied:
        raise GitSafetyError(
            "refuse to stage unsafe or out-of-scope paths: " + ", ".join(denied)
        )
    if not allowed:
        return GitDeployResult(allowed=[], denied=[], commit_message=message)
    if dry_run:
        return GitDeployResult(allowed=allowed, denied=[], commit_message=message)

    add_result = _run_git(root, ["add", "--", *allowed])
    if add_result.returncode != 0:
        raise GitSafetyError(add_result.stderr.strip() or "git add failed")

    check_result = _run_git(root, ["diff", "--cached", "--check"])
    if check_result.returncode != 0:
        raise GitSafetyError(check_result.stdout.strip() or check_result.stderr.strip())

    commit_result = _run_git(root, ["commit", "-m", message])
    if commit_result.returncode != 0:
        raise GitSafetyError(commit_result.stderr.strip() or commit_result.stdout.strip())

    deploy_result = GitDeployResult(
        allowed=allowed,
        denied=[],
        committed=True,
        commit_message=message,
        stdout=commit_result.stdout,
        stderr=commit_result.stderr,
    )
    if push:
        push_result = _run_git(root, push_args or ["push"], timeout=120)
        deploy_result.stdout += push_result.stdout
        deploy_result.stderr += push_result.stderr
        if push_result.returncode != 0:
            raise GitSafetyError(push_result.stderr.strip() or "git push failed")
        deploy_result.pushed = True
    return deploy_result
