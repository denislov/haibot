# -*- coding: utf-8 -*-
"""Tests for external coding CLI tools."""
from __future__ import annotations

import json

import pytest

import haibot.agents.tools.external_cli as external_cli


def _payload(response):
    return json.loads(response.content[0]["text"])


@pytest.mark.asyncio
async def test_external_cli_reports_missing_executable(monkeypatch) -> None:
    monkeypatch.setattr(external_cli.shutil, "which", lambda _name: None)

    response = await external_cli.run_codex_cli("fix bug")
    payload = _payload(response)

    assert payload["provider"] == "codex_cli"
    assert payload["status"] == "unavailable"
    assert payload["exit_code"] == -1


@pytest.mark.asyncio
async def test_external_cli_reports_probe_failure(monkeypatch) -> None:
    monkeypatch.setattr(external_cli.shutil, "which", lambda _name: "/tmp/cli")

    async def fake_probe(_spec, _cwd):
        return False, "failed"

    monkeypatch.setattr(external_cli, "_probe_cli", fake_probe)

    response = await external_cli.run_claude_code_cli("summarize")
    payload = _payload(response)

    assert payload["provider"] == "claude_code_cli"
    assert payload["status"] == "unsupported"
    assert payload["probe"] == "failed"


@pytest.mark.asyncio
async def test_external_cli_reports_timeout(monkeypatch) -> None:
    monkeypatch.setattr(external_cli.shutil, "which", lambda _name: "/tmp/cli")

    async def fake_probe(_spec, _cwd):
        return True, "ok"

    monkeypatch.setattr(external_cli, "_probe_cli", fake_probe)

    async def fake_run(command, cwd, timeout):
        _ = (command, cwd, timeout)
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "Command timed out after 3 seconds.",
            "timed_out": True,
        }

    monkeypatch.setattr(external_cli, "_run_cli_command", fake_run)

    response = await external_cli.run_gemini_cli("test", timeout=3)
    payload = _payload(response)

    assert payload["provider"] == "gemini_cli"
    assert payload["status"] == "timeout"
    assert payload["exit_code"] == -1
    assert "timed out" in payload["stderr"]


@pytest.mark.asyncio
async def test_external_cli_returns_normalized_success_payload(
    monkeypatch,
) -> None:
    monkeypatch.setattr(external_cli.shutil, "which", lambda _name: "/tmp/cli")

    async def fake_probe(_spec, _cwd):
        return True, "ok"

    monkeypatch.setattr(external_cli, "_probe_cli", fake_probe)

    async def fake_run(command, cwd, timeout):
        _ = (cwd, timeout)
        assert "--json" in command
        return {
            "exit_code": 0,
            "stdout": '{"event":"done","message":"Codex transcript"}',
            "stderr": "",
            "timed_out": False,
        }

    monkeypatch.setattr(external_cli, "_run_cli_command", fake_run)

    response = await external_cli.run_codex_cli("implement feature")
    payload = _payload(response)

    assert payload["provider"] == "codex_cli"
    assert payload["status"] == "completed"
    assert payload["exit_code"] == 0
    assert "Codex transcript" in payload["output"]
