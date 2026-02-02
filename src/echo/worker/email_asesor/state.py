import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage


class SummaryState(TypedDict):
    room_id: str
    session_blob: str
    transcription: str
    messages: Annotated[list[BaseMessage], operator.add]
    final_response: str
