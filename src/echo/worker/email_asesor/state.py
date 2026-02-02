from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
import operator

class SummaryState(TypedDict):
    room_id: str
    session_blob: str
    transcription: str
    messages: Annotated[List[BaseMessage], operator.add] 
    final_response: str