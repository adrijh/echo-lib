from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from echo.logger import configure_logger
from echo.worker.email_asesor.nodes import (
    generate_summary,
    load_transcription,
    send_email,
)
from echo.worker.email_asesor.state import SummaryState

logger = configure_logger(__name__)


def build_agent(checkpointer: Any) -> CompiledStateGraph[Any, Any, Any, Any]:
    workflow = StateGraph(SummaryState)

    workflow.add_node("load_transcription", load_transcription)
    workflow.add_node("generate_summary", generate_summary)
    workflow.add_node("send_email", send_email)

    workflow.set_entry_point("load_transcription")
    workflow.add_edge("load_transcription", "generate_summary")
    workflow.add_edge("generate_summary", "send_email")
    workflow.add_edge("send_email", END)

    return workflow.compile(checkpointer=checkpointer)
