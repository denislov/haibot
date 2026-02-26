# -*- coding: utf-8 -*-
# HaiBotAgent is lazy-loaded so that importing agents.skills_manager (e.g.
# from CLI init_cmd/skills_cmd) does not pull react_agent, agentscope, tools.
# pylint: disable=undefined-all-variable
__all__ = ["HaiBotAgent"]


def __getattr__(name: str):
    if name == "HaiBotAgent":
        from .react_agent import HaiBotAgent

        return HaiBotAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
