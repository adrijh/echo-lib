from langgraph.graph import StateGraph, END

from echo.worker.email_asesor.state import SummaryState
from echo.worker.email_asesor.nodes import (
    load_transcription,
    generate_summary,
    send_email,
)
from echo.logger import configure_logger

logger = configure_logger(__name__)


def build_agent(checkpointer):
    logger.info("Building StateGraph...")
    workflow = StateGraph(SummaryState)
    
    workflow.add_node("load_transcription", load_transcription)
    workflow.add_node("generate_summary", generate_summary)
    workflow.add_node("send_email", send_email)
    
    workflow.set_entry_point("load_transcription")
    workflow.add_edge("load_transcription", "generate_summary")
    workflow.add_edge("generate_summary", "send_email")
    workflow.add_edge("send_email", END)
    
    
    return workflow.compile(checkpointer=checkpointer)



