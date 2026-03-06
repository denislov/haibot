# backend/tests/app/test_memory_isolation.py
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


async def test_runner_creates_per_agent_memory_manager(tmp_path):
    """Each agent_id should get its own MemoryManager on first query."""
    workspace = tmp_path / "workspace" / "alice"
    workspace.mkdir(parents=True)

    with patch("haibot.app.runner.runner.WORKING_DIR", tmp_path):
        # Re-import after patch to pick up the patched WORKING_DIR
        import importlib
        import haibot.app.runner.runner as runner_mod
        importlib.reload(runner_mod)

        runner = runner_mod.AgentRunner()
        runner._memory_managers = {}

        with patch.object(runner_mod.MemoryManager, "start", new_callable=AsyncMock):
            mm = await runner._get_or_create_memory_manager("alice")

        assert "alice" in runner._memory_managers
        assert runner._memory_managers["alice"] is mm


async def test_runner_reuses_memory_manager_for_same_agent(tmp_path):
    """Second call for same agent_id returns the cached instance."""
    workspace = tmp_path / "workspace" / "bob"
    workspace.mkdir(parents=True)

    with patch("haibot.app.runner.runner.WORKING_DIR", tmp_path):
        import importlib
        import haibot.app.runner.runner as runner_mod
        importlib.reload(runner_mod)

        runner = runner_mod.AgentRunner()
        runner._memory_managers = {}

        with patch.object(runner_mod.MemoryManager, "start", new_callable=AsyncMock):
            mm1 = await runner._get_or_create_memory_manager("bob")
            mm2 = await runner._get_or_create_memory_manager("bob")

        assert mm1 is mm2


async def test_concurrent_calls_for_same_agent_create_one_instance(tmp_path):
    """Concurrent calls for the same agent_id must not create duplicate MemoryManagers."""
    workspace = tmp_path / "workspace" / "concurrent_agent"
    workspace.mkdir(parents=True)

    with patch("haibot.app.runner.runner.WORKING_DIR", tmp_path):
        import importlib
        import haibot.app.runner.runner as runner_mod
        importlib.reload(runner_mod)

        runner = runner_mod.AgentRunner()
        runner._memory_managers = {}
        runner._mm_locks = {}

        start_call_count = 0

        async def counting_start(self_mm):
            nonlocal start_call_count
            start_call_count += 1
            # Small sleep to allow other coroutine to interleave
            await asyncio.sleep(0)

        with patch.object(runner_mod.MemoryManager, "start", counting_start):
            results = await asyncio.gather(
                runner._get_or_create_memory_manager("concurrent_agent"),
                runner._get_or_create_memory_manager("concurrent_agent"),
            )

        # Only one MemoryManager should have been started
        assert start_call_count == 1, f"Expected 1 start call, got {start_call_count}"
        # Both calls should return the same instance
        assert results[0] is results[1]


async def test_failed_start_not_cached(tmp_path):
    """If mm.start() fails, the broken instance must not be stored in the cache."""
    workspace = tmp_path / "workspace" / "failing_agent"
    workspace.mkdir(parents=True)

    with patch("haibot.app.runner.runner.WORKING_DIR", tmp_path):
        import importlib
        import haibot.app.runner.runner as runner_mod
        importlib.reload(runner_mod)

        runner = runner_mod.AgentRunner()
        runner._memory_managers = {}
        runner._mm_locks = {}

        async def failing_start(self_mm):
            raise RuntimeError("DB connection failed")

        with patch.object(runner_mod.MemoryManager, "start", failing_start):
            mm = await runner._get_or_create_memory_manager("failing_agent")

        # The broken instance must NOT be in the cache
        assert "failing_agent" not in runner._memory_managers
        # But a MemoryManager was still returned (caller handles gracefully)
        assert mm is not None
