# -*- coding: utf-8 -*-
"""Agent hooks package.

This package provides hook implementations for HaiBotAgent that follow
AgentScope's hook interface (any Callable).

Available Hooks:
    - BootstrapHook: First-time setup guidance
    - MemoryCompactionHook: Automatic context window management
"""

from .bootstrap import BootstrapHook
from .memory_compaction import MemoryCompactionHook
from .agent_info import AgentInfoHook
__all__ = [
    "BootstrapHook",
    "MemoryCompactionHook",
    "AgentInfoHook",
]
