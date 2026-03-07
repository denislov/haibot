# -*- coding: utf-8 -*-
# pylint: disable=unused-argument too-many-branches too-many-statements
import asyncio
import json
import logging
from pathlib import Path

from agentscope.message import Msg
from agentscope.pipeline import stream_printing_messages
from agentscope_runtime.engine.runner import Runner
from agentscope_runtime.engine.schemas.agent_schemas import AgentRequest
from dotenv import load_dotenv

from .query_error_dump import write_query_error_dump
from .session import SafeJSONSession
from .utils import build_env_context
from ..channels.schema import DEFAULT_CHANNEL
from ...agents.memory import MemoryManager
from ...agents.react_agent import HaiBotAgent
from ...config import load_config
from ...constant import WORKING_DIR

logger = logging.getLogger(__name__)


class AgentRunner(Runner):
    def __init__(self) -> None:
        super().__init__()
        self.framework_type = "agentscope"
        self._chat_manager = None  # Store chat_manager reference
        self._mcp_manager = None  # MCP client manager for hot-reload

        self._group_chat_repo = None

        self.memory_manager: MemoryManager | None = None
        self._memory_managers: dict[str, MemoryManager] = {}
        self._mm_locks: dict[str, asyncio.Lock] = {}

    async def _get_or_create_memory_manager(self, agent_id: str) -> MemoryManager:
        """Return a started MemoryManager for agent_id, creating if needed. Thread-safe."""
        # Fast path (no lock): already created
        if agent_id in self._memory_managers:
            return self._memory_managers[agent_id]

        # Get or create a per-agent lock (Lock() is synchronous, GIL makes this safe)
        if agent_id not in self._mm_locks:
            self._mm_locks[agent_id] = asyncio.Lock()
        lock = self._mm_locks[agent_id]

        async with lock:
            # Re-check inside lock (another coroutine may have created it while we waited)
            if agent_id in self._memory_managers:
                return self._memory_managers[agent_id]

            workspace_dir = WORKING_DIR / "workspace" / agent_id
            working_dir = str(workspace_dir) if workspace_dir.is_dir() else str(WORKING_DIR)
            mm = MemoryManager(working_dir=working_dir)
            try:
                await mm.start()
                self._memory_managers[agent_id] = mm  # only store on success
            except Exception as e:
                logger.warning("MemoryManager start failed for agent %s: %s", agent_id, e)
                # Don't cache the broken instance — next call will retry
            return mm

    def set_chat_manager(self, chat_manager):
        """Set chat manager for auto-registration.

        Args:
            chat_manager: ChatManager instance
        """
        self._chat_manager = chat_manager

    def set_mcp_manager(self, mcp_manager):
        """Set MCP client manager for hot-reload support.

        Args:
            mcp_manager: MCPClientManager instance
        """
        self._mcp_manager = mcp_manager

    def set_group_chat_repo(self, repo) -> None:
        """Set group chat repository.

        Args:
            repo: GroupChatRepo instance
        """
        self._group_chat_repo = repo

    async def query_handler(
        self,
        msgs,
        request: AgentRequest = None,
        **kwargs,
    ):
        """
        Handle agent query.
        """

        agent = None
        chat = None

        try:
            # Resolve agent_id from request metadata (default: "main")
            agent_id = "main"
            if hasattr(request, "metadata") and isinstance(
                request.metadata, dict
            ):
                agent_id = request.metadata.get("agent_id", "main")
            
            session_id = request.session_id
            user_id = request.user_id
            channel = getattr(request, "channel", DEFAULT_CHANNEL)

            logger.info(
                "Handle agent query:\n%s",
                json.dumps(
                    {
                        "agent_id": agent_id,
                        "session_id": session_id,
                        "user_id": user_id,
                        "channel": channel,
                        "msgs_len": len(msgs) if msgs else 0,
                        "msgs_str": str(msgs)[:300] + "...",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )

            workspace_dir = WORKING_DIR / "workspace" / agent_id

            if not workspace_dir.is_dir():
                workspace_dir = WORKING_DIR

            env_context = build_env_context(
                session_id=session_id,
                user_id=user_id,
                channel=channel,
                working_dir=str(workspace_dir),
            )

            # Get MCP clients from manager (hot-reloadable)
            mcp_clients = []
            if self._mcp_manager is not None:
                mcp_clients = await self._mcp_manager.get_clients()

            # Check for group chat
            group_id = None
            if hasattr(request, "metadata") and isinstance(request.metadata, dict):
                group_id = request.metadata.get("group_id")

            if group_id and self._group_chat_repo is not None:
                config = self._group_chat_repo.get(group_id)
                if config is None:
                    raise ValueError(f"Group chat '{group_id}' not found")

                from ..group_chat.orchestrator import GroupChatOrchestrator

                # Build agent_meta: {agent_id: {name: ...}} for all involved agents
                all_ids = [config.host_agent_id] + config.participant_agent_ids
                agent_meta = {}
                for aid in all_ids:
                    workspace = WORKING_DIR / "workspace" / aid
                    meta_file = workspace / ".agent_meta.json"
                    if meta_file.exists():
                        try:
                            m = json.loads(meta_file.read_text(encoding="utf-8"))
                            agent_meta[aid] = m
                        except Exception:
                            agent_meta[aid] = {"name": aid}
                    else:
                        agent_meta[aid] = {"name": aid}

                _cfg = load_config()
                language = getattr(getattr(_cfg, "agents", None), "language", "zh")

                orchestrator = GroupChatOrchestrator(
                    config=config,
                    agent_meta=agent_meta,
                    memory_manager_factory=self._get_or_create_memory_manager,
                    mcp_clients=mcp_clients,
                    env_context_factory=build_env_context,
                    language=language,
                )

                async for msg, last in orchestrator.run(
                    user_msg=msgs[0] if msgs else Msg("user", "", "user"),
                    session_id=session_id,
                    user_id=user_id,
                    channel=channel,
                ):
                    yield msg, last
                return

            config = load_config()
            max_iters = config.agents.running.max_iters
            max_input_length = config.agents.running.max_input_length

            memory_manager = await self._get_or_create_memory_manager(agent_id)

            agent = HaiBotAgent(
                env_context=env_context,
                mcp_clients=mcp_clients,
                memory_manager=memory_manager,
                max_iters=max_iters,
                max_input_length=max_input_length,
                agent_id=agent_id,
            )
            # logger.info(
            #     "agent prompt:\n%s",
            #     agent.sys_prompt
            # )
            await agent.register_mcp_clients()
            agent.set_console_output_enabled(enabled=False)

            logger.debug(
                f"Agent Query msgs {msgs}",
            )

            name = "New Chat"
            if len(msgs) > 0:
                content = msgs[0].get_text_content()
                if content:
                    name = msgs[0].get_text_content()[:10]
                else:
                    name = "Media Message"

            if self._chat_manager is not None:
                chat = await self._chat_manager.get_or_create_chat(
                    session_id,
                    user_id,
                    channel,
                    name=name,
                )

            await self.session.load_session_state(
                session_id=session_id,
                user_id=user_id,
                agent=agent,
            )

            # Rebuild system prompt so it always reflects the latest
            # AGENTS.md / SOUL.md / PROFILE.md, not the stale one saved
            # in the session state.
            agent.rebuild_sys_prompt()

            async for msg, last in stream_printing_messages(
                agents=[agent],
                coroutine_task=agent(msgs),
            ):
                yield msg, last

        except asyncio.CancelledError:
            if agent is not None:
                await agent.interrupt()
            raise
        except Exception as e:
            debug_dump_path = write_query_error_dump(
                request=request,
                exc=e,
                locals_=locals(),
            )
            path_hint = (
                f"\n(Details:  {debug_dump_path})" if debug_dump_path else ""
            )
            logger.exception(f"Error in query handler: {e}{path_hint}")
            if debug_dump_path:
                setattr(e, "debug_dump_path", debug_dump_path)
                if hasattr(e, "add_note"):
                    e.add_note(
                        f"(Details:  {debug_dump_path})",
                    )
                suffix = f"\n(Details:  {debug_dump_path})"
                e.args = (
                    (f"{e.args[0]}{suffix}" if e.args else suffix.strip()),
                ) + e.args[1:]
            raise
        finally:
            if agent is not None:
                await self.session.save_session_state(
                    session_id=session_id,
                    user_id=user_id,
                    agent=agent,
                )

            if self._chat_manager is not None and chat is not None:
                await self._chat_manager.update_chat(chat)

    async def init_handler(self, *args, **kwargs):
        """
        Init handler.
        """
        # Load environment variables from .env file
        env_path = Path(__file__).resolve().parents[4] / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug(f"Loaded environment variables from {env_path}")
        else:
            logger.debug(
                f".env file not found at {env_path}, "
                "using existing environment variables",
            )

        session_dir = str(WORKING_DIR / "sessions")
        self.session = SafeJSONSession(save_dir=session_dir)

        try:
            main_mm = await self._get_or_create_memory_manager("main")
            self.memory_manager = main_mm  # backward compat
        except Exception as e:
            logger.exception(f"MemoryManager start failed: {e}")

    async def shutdown_handler(self, *args, **kwargs):
        """Shutdown handler."""
        for agent_id, mm in list(self._memory_managers.items()):
            try:
                await mm.close()
            except Exception as e:
                logger.warning("MemoryManager stop failed for %s: %s", agent_id, e)
        self._memory_managers.clear()
