# backend/tests/group_chat/test_stream_merger.py
import asyncio
import pytest
from haibot.app.group_chat.stream_merger import merge_streams


async def _gen(items, delay=0):
    for item in items:
        if delay:
            await asyncio.sleep(delay)
        yield item


async def test_merge_single_stream():
    results = []
    async for item in merge_streams([_gen([1, 2, 3])]):
        results.append(item)
    assert results == [1, 2, 3]


async def test_merge_two_sequential_streams():
    results = []
    async for item in merge_streams([_gen([1, 2]), _gen([3, 4])]):
        results.append(item)
    assert sorted(results) == [1, 2, 3, 4]


async def test_merge_empty():
    results = []
    async for item in merge_streams([]):
        results.append(item)
    assert results == []


async def test_merge_preserves_all_items():
    """All items from all streams must appear in output."""
    stream_a = _gen(["a1", "a2", "a3"])
    stream_b = _gen(["b1", "b2"])
    results = []
    async for item in merge_streams([stream_a, stream_b]):
        results.append(item)
    assert sorted(results) == ["a1", "a2", "a3", "b1", "b2"]
