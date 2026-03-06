# backend/tests/group_chat/test_mention_parser.py
import pytest
from haibot.app.group_chat.mention_parser import parse_mentions, resolve_mentions


def test_parse_simple_mentions():
    text = "让我们听听 @analyst 和 @coder 的意见"
    assert parse_mentions(text) == ["analyst", "coder"]


def test_parse_chinese_names():
    text = "请 @分析师 先发言"
    assert parse_mentions(text) == ["分析师"]


def test_parse_no_mentions():
    assert parse_mentions("这个问题我来回答") == []


def test_parse_deduplicates():
    text = "@alpha 说完再请 @alpha 补充"
    assert parse_mentions(text) == ["alpha"]


def test_resolve_by_agent_id():
    participants = [
        {"id": "analyst", "name": "分析师"},
        {"id": "coder", "name": "程序员"},
    ]
    result = resolve_mentions(["analyst"], participants)
    assert result == ["analyst"]


def test_resolve_by_display_name():
    participants = [
        {"id": "analyst", "name": "分析师"},
    ]
    result = resolve_mentions(["分析师"], participants)
    assert result == ["analyst"]


def test_resolve_unknown_name_ignored():
    participants = [{"id": "analyst", "name": "分析师"}]
    result = resolve_mentions(["unknown"], participants)
    assert result == []


def test_resolve_mixed():
    participants = [
        {"id": "analyst", "name": "分析师"},
        {"id": "coder", "name": "程序员"},
    ]
    result = resolve_mentions(["analyst", "程序员", "ghost"], participants)
    assert result == ["analyst", "coder"]
