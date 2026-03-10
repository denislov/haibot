# -*- coding: utf-8 -*-
"""GroupChatOrchestrator: manages multi-agent group chat rounds."""
import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Callable

from agentscope.message import Msg
from agentscope.pipeline import stream_printing_messages

from .mention_parser import parse_mentions, resolve_mentions
from .models import GroupChatConfig
from .stream_merger import merge_streams
from ...agents.react_agent import HaiBotAgent
from ...constant import WORKING_DIR

logger = logging.getLogger(__name__)


def tag_event(event: dict, agent_id: str, agent_name: str) -> dict:
    """Return a copy of event with agent_id and agent_name added."""
    return {**event, "agent_id": agent_id, "agent_name": agent_name}


async def stream_agent(
    agent: HaiBotAgent,
    msgs: list[Msg],
    agent_id: str,
    agent_name: str,
) -> AsyncGenerator[tuple[Msg, bool], None]:
    """Stream one agent's response, injecting agent_id/name into msg.metadata.

    Yields (Msg, bool) pairs compatible with agentscope runtime's stream adapter.
    The agent_id and agent_name are set in msg.metadata for frontend routing.
    """
    async for msg, last in stream_printing_messages(
        agents=[agent],
        coroutine_task=agent(msgs),
    ):
        if isinstance(msg, Msg):
            if msg.metadata is None:
                msg.metadata = {}
            if isinstance(msg.metadata, dict):
                msg.metadata.setdefault("agent_id", agent_id)
                msg.metadata.setdefault("agent_name", agent_name)
            yield msg, last


def _build_group_host_context(
    config: GroupChatConfig,
    round_index: int,
    agent_meta: dict[str, dict],
    language: str,
) -> str:
    """Build the GROUP_HOST.md injection string for this round."""
    template_path = (
        Path(__file__).resolve().parents[2]
        / "agents" / "md_files" / language / "GROUP_HOST.md"
    )
    if not template_path.exists():
        template_path = (
            Path(__file__).resolve().parents[2]
            / "agents" / "md_files" / "zh" / "GROUP_HOST.md"
        )

    template = template_path.read_text(encoding="utf-8") if template_path.exists() else ""

    participant_lines = []
    for pid in config.participant_agent_ids:
        pname = agent_meta.get(pid, {}).get("name", pid)
        participant_lines.append(f"- @{pname} ({pid})")
    participant_list = "\n".join(participant_lines)

    return template.format(
        participant_list=participant_list,
        round_index=round_index + 1,
        max_rounds=config.max_rounds,
    )


class GroupChatOrchestrator:
    """Manages multi-agent group chat: host routing, participant concurrency."""

    def __init__(
        self,
        config: GroupChatConfig,
        agent_meta: dict[str, dict],
        memory_manager_factory: Callable,
        mcp_clients: list[Any],
        env_context_factory: Callable,
        language: str = "zh",
    ) -> None:
        self._config = config
        self._agent_meta = agent_meta
        self._mm_factory = memory_manager_factory
        self._mcp_clients = mcp_clients
        self._env_ctx_factory = env_context_factory
        self._language = language

    def _get_participant_info(self) -> list[dict]:
        return [
            {"id": pid, "name": self._agent_meta.get(pid, {}).get("name", pid)}
            for pid in self._config.participant_agent_ids
        ]

    async def _make_agent(
        self,
        agent_id: str,
        extra_sys_context: str = "",
        session_id: str = "",
        user_id: str = "",
        channel: str = "console",
    ) -> HaiBotAgent:
        workspace_dir = WORKING_DIR / "workspace" / agent_id
        if not workspace_dir.is_dir():
            workspace_dir = WORKING_DIR

        env_context = self._env_ctx_factory(
            session_id=session_id,
            user_id=user_id,
            channel=channel,
            working_dir=str(workspace_dir),
        )
        if extra_sys_context:
            env_context = extra_sys_context + "\n\n" + (env_context or "")

        memory_manager = await self._mm_factory(agent_id)

        return HaiBotAgent(
            env_context=env_context,
            mcp_clients=self._mcp_clients,
            memory_manager=memory_manager,
            agent_id=agent_id,
            workspace_dir=workspace_dir,
            enable_memory_manager=(memory_manager is not None),
        )

    async def run(
        self,
        user_msg: Msg,
        session_id: str,
        user_id: str,
        channel: str,
    ) -> AsyncGenerator[tuple[Msg, bool], None]:
        """Run the group chat loop, yielding (Msg, bool) pairs."""
        config = self._config
        participant_info = self._get_participant_info()
        history: list[Msg] = [user_msg]
        self.final_history: list[Msg] = []

        for round_index in range(config.max_rounds):
            # ── 1. Host turn ──────────────────────────────────────────────
            host_context = _build_group_host_context(
                config, round_index, self._agent_meta, self._language
            )
            host_name = self._agent_meta.get(config.host_agent_id, {}).get(
                "name", config.host_agent_id
            )
            host = await self._make_agent(
                config.host_agent_id,
                extra_sys_context=host_context,
                session_id=session_id,
                user_id=user_id,
                channel=channel,
            )
            await host.register_mcp_clients()
            host.set_console_output_enabled(enabled=False)

            host_final: Msg | None = None
            async for msg, last in stream_agent(
                host, list(history), config.host_agent_id, host_name
            ):
                yield msg, last
                if last:
                    host_final = msg

            if host_final is None:
                break

            history.append(host_final)

            # ── 2. Parse @mentions ────────────────────────────────────────
            text = host_final.get_text_content() or ""
            raw_names = parse_mentions(text)
            mentioned_ids = resolve_mentions(raw_names, participant_info)

            if not mentioned_ids:
                break  # Host chose to end discussion

            # ── 3. Participant turn (concurrent) ──────────────────────────
            participant_finals: list[Msg] = []

            async def _participant_stream(pid: str):
                pname = self._agent_meta.get(pid, {}).get("name", pid)
                p_agent = await self._make_agent(
                    pid,
                    session_id=session_id,
                    user_id=user_id,
                    channel=channel,
                )
                await p_agent.register_mcp_clients()
                p_agent.set_console_output_enabled(enabled=False)
                async for item in stream_agent(p_agent, list(history), pid, pname):
                    yield item

            participant_streams = [_participant_stream(pid) for pid in mentioned_ids]

            async for item in merge_streams(participant_streams):
                msg, last = item
                yield msg, last
                if last:
                    participant_finals.append(msg)

            history.extend(participant_finals)
        self.final_history = list(history)
        # Stream ends naturally — no synthetic group_done event needed
