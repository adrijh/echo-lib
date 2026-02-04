import asyncio
import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import APIRouter, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

import echo.events.v1 as events
from echo import config as cfg
from echo.logger import configure_logger
from echo.utils import db
from echo.utils.storage import get_blob_content
from echo.worker.queue import QueueWorker, RabbitQueue

log = configure_logger(__name__)

WS_REFRESH_TIME_SECONDS = 5

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    log.info("Setting up worker...")

    queue = await RabbitQueue.build()
    worker = QueueWorker(queue)
    await worker.start()
    yield
    await worker.stop()


app = FastAPI(lifespan=lifespan)
api = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/health", tags=["health"])
def healthcheck() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )


@api.get("/report/{room_id}")
async def get_room_report(room_id: str) -> JSONResponse:
    blob_url = f"https://{cfg.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{cfg.AZURE_CONTAINER}/recordings/{room_id}/session-report.json"
    content = await get_blob_content(blob_url)

    if not content:
        raise HTTPException(status_code=204, detail="Report not found")

    report = json.loads(content.decode("utf-8"))
    return JSONResponse(
        status_code=200,
        content=report,
    )


@api.get("/recording/{room_id}")
async def get_room_recording(room_id: str) -> StreamingResponse:
    blob_url = f"https://{cfg.AZURE_ACCOUNT_NAME}.blob.core.windows.net/{cfg.AZURE_CONTAINER}/recordings/{room_id}/recording.ogg"
    content = await get_blob_content(blob_url)

    if not content:
        raise HTTPException(status_code=204, detail="Recording not found")

    return StreamingResponse(
        BytesIO(content),
        media_type="audio/ogg",
        headers={
            "Content-Disposition": "inline; filename=recording.ogg"
        },
    )


@api.post("/sessions")
async def start_session(data: events.StartSessionRequest | list[events.StartSessionRequest]) -> JSONResponse:
    queue = await RabbitQueue.build()
    if isinstance(data, list):
        for event in data:
            await queue.send_event(event)
        msg_response = f"Session start requested for {len(data)} rooms"
    else:
        await queue.send_event(data)
        msg_response = f"Session start requested for room_id: {data.room_id}"
    await queue.stop()
    return JSONResponse(
        status_code=200,
        content={"message": msg_response},
    )


@app.websocket("/api")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    log.info("WebSocket client connected")

    try:
        while True:
            rooms = db.get_rooms()
            await websocket.send_json({"rooms": [room.model_dump_json() for room in rooms]})
            await asyncio.sleep(WS_REFRESH_TIME_SECONDS)
    except WebSocketDisconnect:
        log.info("WebSocket client disconnected normally")
    except Exception as e:
        log.error(f"WebSocket error: {e}")


app.include_router(api, prefix="/api")
