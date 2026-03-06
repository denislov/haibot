# -*- coding: utf-8 -*-
"""Parse @mention tokens from agent reply text."""
import re


# Matches @word where word includes ASCII alphanumerics/underscore/hyphen
# and CJK unified ideographs (U+4E00–U+9FFF)
_MENTION_RE = re.compile(r"@([\w\u4e00-\u9fff]+)")


def parse_mentions(text: str) -> list[str]:
    """Extract unique @mentioned names from text, in order of first appearance."""
    seen: list[str] = []
    for match in _MENTION_RE.finditer(text):
        name = match.group(1)
        if name not in seen:
            seen.append(name)
    return seen


def resolve_mentions(
    raw_names: list[str],
    participants: list[dict],
) -> list[str]:
    """Map raw @mention names to agent IDs.

    Matches by agent ``id`` first, then by ``name`` field (case-insensitive).
    Unknown names are silently dropped.

    Args:
        raw_names: Strings extracted by parse_mentions().
        participants: List of dicts with ``id`` and ``name`` keys.

    Returns:
        Ordered, deduplicated list of resolved agent IDs.
    """
    id_set = {p["id"] for p in participants}
    name_to_id = {p["name"].lower(): p["id"] for p in participants}

    result: list[str] = []
    seen: set[str] = set()

    for name in raw_names:
        if name in id_set:
            agent_id = name
        else:
            agent_id = name_to_id.get(name.lower())

        if agent_id and agent_id not in seen:
            result.append(agent_id)
            seen.add(agent_id)

    return result
