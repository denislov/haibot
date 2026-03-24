# -*- coding: utf-8 -*-
"""In-memory registry for group chat delegation callbacks."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Optional
from uuid import uuid4

_CALLBACKS: dict[str, Callable[[str, str], Awaitable[str]]] = {}


def register_delegate_callback(
    callback: Callable[[str, str], Awaitable[str]],
) -> str:
    """Register callback and return an opaque token."""
    token = uuid4().hex
    _CALLBACKS[token] = callback
    return token


def get_delegate_callback(
    token: str,
) -> Optional[Callable[[str, str], Awaitable[str]]]:
    """Return registered callback for token, if any."""
    return _CALLBACKS.get(token)


def unregister_delegate_callback(token: str) -> None:
    """Remove callback token from registry."""
    _CALLBACKS.pop(token, None)
