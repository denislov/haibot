# backend/tests/group_chat/test_repo.py
import pytest
from pathlib import Path
from haibot.app.group_chat.models import GroupChatConfig
from haibot.app.group_chat.repo import GroupChatRepo


def test_create_and_get(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    cfg = GroupChatConfig(
        id="team_alpha",
        name="Team Alpha",
        host_agent_id="main",
        participant_agent_ids=["analyst", "coder"],
    )
    repo.save(cfg)
    result = repo.get("team_alpha")
    assert result is not None
    assert result.name == "Team Alpha"
    assert result.participant_agent_ids == ["analyst", "coder"]


def test_list(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    repo.save(GroupChatConfig(id="g1", name="G1", host_agent_id="main", participant_agent_ids=[]))
    repo.save(GroupChatConfig(id="g2", name="G2", host_agent_id="main", participant_agent_ids=[]))
    assert len(repo.list()) == 2


def test_delete(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    repo.save(GroupChatConfig(id="g1", name="G1", host_agent_id="main", participant_agent_ids=[]))
    assert repo.delete("g1") is True
    assert repo.get("g1") is None


def test_delete_missing_returns_false(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    assert repo.delete("nonexistent") is False


def test_get_missing_returns_none(tmp_path):
    repo = GroupChatRepo(path=tmp_path / "group_chats.json")
    assert repo.get("missing") is None
