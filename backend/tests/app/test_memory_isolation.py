# backend/tests/app/test_memory_isolation.py
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
