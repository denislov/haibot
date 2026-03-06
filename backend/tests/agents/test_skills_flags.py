# backend/tests/agents/test_skills_flags.py
import json
import pytest
from pathlib import Path


def test_get_agent_skills_config_reads_meta(tmp_path):
    """Should read skills_config from .agent_meta.json."""
    meta = {"name": "Test", "skills_config": {"web_search": False, "code_runner": True}}
    (tmp_path / ".agent_meta.json").write_text(json.dumps(meta))

    from haibot.agents.skills_manager import get_agent_skills_config
    config = get_agent_skills_config(workspace_dir=tmp_path)
    assert config == {"web_search": False, "code_runner": True}


def test_get_agent_skills_config_missing_meta(tmp_path):
    """Missing .agent_meta.json returns empty dict (all skills enabled by default)."""
    from haibot.agents.skills_manager import get_agent_skills_config
    config = get_agent_skills_config(workspace_dir=tmp_path)
    assert config == {}


def test_filter_skills_by_config():
    """Skills disabled in config should be excluded from list."""
    from haibot.agents.skills_manager import filter_skills_by_config
    skills = ["web_search", "code_runner", "browser_use"]
    config = {"web_search": False, "browser_use": False}
    result = filter_skills_by_config(skills, config)
    assert result == ["code_runner"]


def test_filter_skills_empty_config_enables_all():
    """Empty config means all skills pass through."""
    from haibot.agents.skills_manager import filter_skills_by_config
    skills = ["web_search", "code_runner"]
    assert filter_skills_by_config(skills, {}) == skills


def test_filter_skills_absent_key_defaults_to_enabled():
    """Skills not in config are enabled by default."""
    from haibot.agents.skills_manager import filter_skills_by_config
    skills = ["skill_a", "skill_b", "skill_c"]
    config = {"skill_b": False}  # only skill_b explicitly disabled
    result = filter_skills_by_config(skills, config)
    assert result == ["skill_a", "skill_c"]
