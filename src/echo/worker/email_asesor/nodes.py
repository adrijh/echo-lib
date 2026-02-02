import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from echo.worker.email_asesor.state import SummaryState

from echo.utils.storage import get_blob_content
from echo.utils.twilio import TwilioService
from echo.logger import configure_logger

import echo.config as cfg

logger = configure_logger(__name__)

async def load_transcription(state: SummaryState):
    room_id = state.get("room_id")
    blob_url = state.get("session_blob")
    
    logger.info(f"Node 1: Preparing context for Room {room_id}")

    force_mock = os.getenv("USE_MOCK_STORAGE", "false").lower() == "true"

    content = await get_blob_content(blob_url)

    logger.info(f"Transcription loaded ({len(content)} chars): {content[:50]}...") 
    
    return {"transcription": content}

async def generate_summary(state: SummaryState):
    logger.info("Node 2: Summarizing transcription...")
    
    if "Error" in state.get("final_response", ""):
        return {}

    llm = build_mini_model()
    
    system_prompt = (
        "Eres un asistente profesional bilingüe. Tu tarea es resumir la transcripción de la reunión "
        "proporcionada de forma clara, concisa y profesional, exclusivamente en ESPAÑOL. "
        "Usa viñetas para los puntos clave y negritas para los nombres o decisiones importantes."
    )
    user_content = f"Transcription: {state.get('transcription')}"
    
    response = await llm.ainvoke([
        ("system", system_prompt),
        ("user", user_content)
    ])

    logger.info(f"Summary generated: {response.content[:50]}...")

    return {
        "messages": [response], 
        "final_response": response.content
    }

async def send_email(state: SummaryState):
    email_service = TwilioService()

    room_id = state.get("room_id")
    summary_markdown = state.get("final_response")
    raw_text = state.get("transcription")
    
    logger.info(f"Node 3: Dispatching summary for Room {room_id}")
    
    if summary_markdown:
        email_service.send_summary_email(
            subject=f"Meeting Summary: Room {room_id}",
            email_to=cfg.SENDGRID_MAIL_TO,
            content_markdown=summary_markdown,
            attachment_content=raw_text # This adds the .txt file
        )
    
    return {}

def build_mini_model() -> ChatModel:
    return ChatOpenAI(
        model=cfg.OPENAI_MODEL_MINI,
        api_key=SecretStr(cfg.OPENAI_API_KEY),
        temperature=1,
        timeout=100,
        max_retries=5,
    )