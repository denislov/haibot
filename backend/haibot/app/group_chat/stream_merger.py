# -*- coding: utf-8 -*-
"""Merge multiple async generators into one via asyncio.Queue."""
import asyncio
from typing import Any, AsyncGenerator, AsyncIterable


async def merge_streams(
    streams: list[AsyncIterable[Any]],
) -> AsyncGenerator[Any, None]:
    """Merge N async iterables into one, interleaved as items arrive.

    Args:
        streams: List of async iterables to merge.

    Yields:
        Items from any stream in arrival order.
    """
    if not streams:
        return

    queue: asyncio.Queue = asyncio.Queue()
    _SENTINEL = object()
    remaining = len(streams)

    async def _drain(stream: AsyncIterable[Any]) -> None:
        try:
            async for item in stream:
                await queue.put(item)
        finally:
            await queue.put(_SENTINEL)

    tasks = [asyncio.create_task(_drain(s)) for s in streams]

    try:
        while remaining > 0:
            item = await queue.get()
            if item is _SENTINEL:
                remaining -= 1
            else:
                yield item
    except asyncio.CancelledError:
        for t in tasks:
            t.cancel()
        raise
