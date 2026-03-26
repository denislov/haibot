# -*- coding: utf-8 -*-
"""Dedicated wrappers for external coding CLIs."""
from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import signal
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from ...config.context import get_current_workspace_dir
from ...constant import WORKING_DIR
from .shell import smart_decode

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExternalCliSpec:
    """Runtime configuration for one external coding CLI."""

    provider: str
    executable: str
    probe_command: tuple[str, ...]
    build_command: Callable[[str, Path, Optional[str]], list[str]]
    allow_probe_timeout: bool = False


def _resolve_working_dir(cwd: Optional[str]) -> Path:
    """Resolve execution cwd against the active workspace."""
    if cwd:
        return Path(cwd).expanduser().resolve()
    return (get_current_workspace_dir() or WORKING_DIR).expanduser().resolve()


def _tool_response(payload: dict) -> ToolResponse:
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=json.dumps(payload, ensure_ascii=False, indent=2),
            ),
        ],
    )


def _error_payload(
    provider: str,
    command: list[str],
    cwd: Path,
    status: str,
    output: str,
    *,
    exit_code: int = -1,
    stderr: str = "",
    probe: str = "not_run",
) -> ToolResponse:
    return _tool_response(
        {
            "provider": provider,
            "command": " ".join(command),
            "cwd": str(cwd),
            "status": status,
            "exit_code": exit_code,
            "output": output,
            "stderr": stderr,
            "probe": probe,
        },
    )


async def _run_cli_command(
    command: list[str],
    cwd: Path,
    timeout: int,
) -> dict[str, object]:
    """Run one CLI command and capture stdout/stderr."""
    env = os.environ.copy()
    python_bin_dir = str(Path(sys.executable).parent)
    existing_path = env.get("PATH", "")
    env["PATH"] = (
        python_bin_dir + os.pathsep + existing_path
        if existing_path
        else python_bin_dir
    )

    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd),
        env=env,
        start_new_session=sys.platform != "win32",
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout,
        )
        return {
            "exit_code": proc.returncode if proc.returncode is not None else -1,
            "stdout": smart_decode(stdout),
            "stderr": smart_decode(stderr),
            "timed_out": False,
        }
    except asyncio.TimeoutError:
        try:
            if sys.platform != "win32":
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()
            await asyncio.wait_for(proc.wait(), timeout=2)
        except (asyncio.TimeoutError, ProcessLookupError, OSError):
            try:
                if sys.platform != "win32":
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                else:
                    proc.kill()
            except (ProcessLookupError, OSError):
                pass
            try:
                await asyncio.wait_for(proc.wait(), timeout=2)
            except asyncio.TimeoutError:
                logger.warning("Timed out waiting for CLI process to exit")

        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout} seconds.",
            "timed_out": True,
        }


async def _probe_cli(spec: ExternalCliSpec, cwd: Path) -> tuple[bool, str]:
    """Best-effort non-interactive support probe."""
    result = await _run_cli_command(list(spec.probe_command), cwd, timeout=3)
    if result["timed_out"]:
        if spec.allow_probe_timeout:
            return True, "timed_out_but_allowed"
        return False, "timed_out"

    if int(result["exit_code"]) != 0:
        return False, "failed"

    return True, "ok"


def _build_claude_command(
    prompt: str,
    cwd: Path,
    model: Optional[str],
) -> list[str]:
    command = [
        "claude",
        "--print",
        "--output-format",
        "stream-json",
        "--include-partial-messages",
        "--no-session-persistence",
        "--permission-mode",
        "dontAsk",
        "--add-dir",
        str(cwd),
    ]
    if model:
        command.extend(["--model", model])
    command.append(prompt)
    return command


def _build_codex_command(
    prompt: str,
    cwd: Path,
    model: Optional[str],
) -> list[str]:
    command = [
        "codex",
        "exec",
        "--json",
        "--full-auto",
        "--skip-git-repo-check",
        "-C",
        str(cwd),
    ]
    if model:
        command.extend(["-m", model])
    command.append(prompt)
    return command


def _build_gemini_command(
    prompt: str,
    cwd: Path,
    model: Optional[str],
) -> list[str]:
    command = [
        "gemini",
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--approval-mode",
        "auto_edit",
        "--include-directories",
        str(cwd),
    ]
    if model:
        command.extend(["--model", model])
    return command


_SPECS = {
    "claude_code_cli": ExternalCliSpec(
        provider="claude_code_cli",
        executable="claude",
        probe_command=("claude", "--help"),
        build_command=_build_claude_command,
    ),
    "codex_cli": ExternalCliSpec(
        provider="codex_cli",
        executable="codex",
        probe_command=("codex", "exec", "--help"),
        build_command=_build_codex_command,
    ),
    "gemini_cli": ExternalCliSpec(
        provider="gemini_cli",
        executable="gemini",
        probe_command=("gemini", "--help"),
        build_command=_build_gemini_command,
        allow_probe_timeout=True,
    ),
}


async def _execute_external_cli(
    spec: ExternalCliSpec,
    *,
    prompt: str,
    cwd: Optional[str] = None,
    timeout: int = 300,
    model: Optional[str] = None,
) -> ToolResponse:
    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        timeout = 300

    if not prompt.strip():
        return _error_payload(
            spec.provider,
            [spec.executable],
            _resolve_working_dir(cwd),
            "invalid_input",
            "Prompt is empty.",
        )

    working_dir = _resolve_working_dir(cwd)
    if not working_dir.exists():
        return _error_payload(
            spec.provider,
            [spec.executable],
            working_dir,
            "invalid_input",
            f"Working directory does not exist: {working_dir}",
        )

    executable_path = shutil.which(spec.executable)
    if not executable_path:
        return _error_payload(
            spec.provider,
            [spec.executable],
            working_dir,
            "unavailable",
            f"{spec.executable} is not installed or not on PATH.",
        )

    cli_command = spec.build_command(prompt, working_dir, model)
    probe_ok, probe_status = await _probe_cli(spec, working_dir)
    if not probe_ok:
        return _error_payload(
            spec.provider,
            cli_command,
            working_dir,
            "unsupported",
            f"{spec.executable} did not pass the non-interactive probe.",
            probe=probe_status,
        )

    try:
        result = await _run_cli_command(cli_command, working_dir, timeout=timeout)
    except FileNotFoundError:
        return _error_payload(
            spec.provider,
            cli_command,
            working_dir,
            "unavailable",
            f"{spec.executable} could not be started.",
            probe=probe_status,
        )

    status = "completed"
    if result["timed_out"]:
        status = "timeout"
    elif int(result["exit_code"]) != 0:
        status = "failed"

    return _tool_response(
        {
            "provider": spec.provider,
            "command": " ".join(cli_command),
            "cwd": str(working_dir),
            "status": status,
            "exit_code": int(result["exit_code"]),
            "output": result["stdout"],
            "stderr": result["stderr"],
            "probe": probe_status,
            "executable_path": executable_path,
        },
    )


async def run_claude_code_cli(
    prompt: str,
    cwd: Optional[str] = None,
    timeout: int = 300,
    model: Optional[str] = None,
) -> ToolResponse:
    """Run Claude Code CLI non-interactively."""
    return await _execute_external_cli(
        _SPECS["claude_code_cli"],
        prompt=prompt,
        cwd=cwd,
        timeout=timeout,
        model=model,
    )


async def run_codex_cli(
    prompt: str,
    cwd: Optional[str] = None,
    timeout: int = 300,
    model: Optional[str] = None,
) -> ToolResponse:
    """Run Codex CLI non-interactively."""
    return await _execute_external_cli(
        _SPECS["codex_cli"],
        prompt=prompt,
        cwd=cwd,
        timeout=timeout,
        model=model,
    )


async def run_gemini_cli(
    prompt: str,
    cwd: Optional[str] = None,
    timeout: int = 300,
    model: Optional[str] = None,
) -> ToolResponse:
    """Run Gemini CLI non-interactively."""
    return await _execute_external_cli(
        _SPECS["gemini_cli"],
        prompt=prompt,
        cwd=cwd,
        timeout=timeout,
        model=model,
    )
