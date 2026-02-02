from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver

from echo.logger import configure_logger
from echo.worker.email_asesor.agent import build_agent

logger = configure_logger(__name__)


checkpointer = MemorySaver()
agent = build_agent(checkpointer)


async def run_email_asesor_workflow(event_data: dict[str, Any]) -> None:
    try:
        room_id = event_data.get("room_id")
        session_blob = event_data.get("session_blob")

        if not room_id or not session_blob:
            logger.error(f"Missing required data in event: {event_data}")
            return

        initial_state = {
            "room_id": room_id,
            "session_blob": session_blob,
            "messages": []
        }

        config = RunnableConfig(configurable={"thread_id": room_id})
        await agent.ainvoke(initial_state, config)

    except Exception as e:
        logger.error(f"Error in Email Asesor Graph: {e}")
