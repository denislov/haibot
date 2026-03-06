# backend/tests/agents/test_workspace_isolation.py
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_haibot_agent_uses_explicit_workspace_dir(tmp_path):
    """HaiBotAgent should use explicit workspace_dir for tool presets."""
    workspace = tmp_path / "my_agent"
    workspace.mkdir()

    with (
        patch("haibot.agents.react_agent.create_model_and_formatter") as mock_factory,
        patch("haibot.agents.react_agent.ensure_skills_initialized"),
        patch("haibot.agents.react_agent.list_available_skills", return_value=[]),
        patch("haibot.agents.react_agent.build_system_prompt_for_agent", return_value="sys"),
        patch("haibot.agents.react_agent.load_config"),
    ):
        mock_factory.return_value = (MagicMock(), MagicMock())
        from haibot.agents.react_agent import HaiBotAgent
        agent = HaiBotAgent(agent_id="my_agent", workspace_dir=workspace)
        assert agent._workspace_dir == workspace


def test_haibot_agent_defaults_workspace_dir_from_agent_id(tmp_path):
    """Without explicit workspace_dir, should fall back to WORKING_DIR/workspace/agent_id or WORKING_DIR."""
    with (
        patch("haibot.agents.react_agent.create_model_and_formatter") as mock_factory,
        patch("haibot.agents.react_agent.ensure_skills_initialized"),
        patch("haibot.agents.react_agent.list_available_skills", return_value=[]),
        patch("haibot.agents.react_agent.build_system_prompt_for_agent", return_value="sys"),
        patch("haibot.agents.react_agent.load_config"),
        patch("haibot.agents.react_agent.WORKING_DIR", tmp_path),
    ):
        mock_factory.return_value = (MagicMock(), MagicMock())
        from haibot.agents.react_agent import HaiBotAgent
        agent = HaiBotAgent(agent_id="main")
        # Falls back to WORKING_DIR when workspace/main doesn't exist
        assert agent._workspace_dir in (tmp_path / "workspace" / "main", tmp_path)
