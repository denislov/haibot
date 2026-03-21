import logging
from typing import Any

logger = logging.getLogger(__name__)

class AgentInfoHook:
    """Hook for bootstrap guidance on first user interaction.

    This hook looks for a BOOTSTRAP.md file in the working directory
    and if found, prepends guidance to the first user message to help
    establish the agent's identity and user preferences.
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
    ):
        """Initialize bootstrap hook.

        Args:
            agent_id: Agent ID
            agent_name: Agent name
        """
        self.agent_id = agent_id
        self.agent_name = agent_name

    async def post_reply(
        self,
        agent,
        kwargs: dict[str, Any],
        output: Any,
    ) -> Any | None:
        if hasattr(output, "metadata"):
            if output.metadata is None:
                output.metadata = {}
            output.metadata["agent_id"] = self.agent_id
            output.metadata["agent_name"] = self.agent_name
            logger.info(f"Agent Msg: {output}")
        return output

    async def pre_observe(self, agent, kwargs: dict[str, Any]) -> Any | None:
        if hasattr(kwargs, "msg"):
            msg = kwargs["msg"]
            if msg.metadata is None:
                msg.metadata = {}
            msg.metadata["agent_id"] = self.agent_id
            msg.metadata["agent_name"] = self.agent_name
            logger.info(f"Agent Msg: {msg}")
            return {
            **kwargs,
            "msg": msg,
        }