import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import echo.events.v1 as events
from echo.logger import configure_logger
from echo.utils import db
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


@api.get("/sessions")
async def list_sessions() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=[],
    )


@api.post("/sessions")
async def start_session(data: events.StartSessionRequest | list[events.StartSessionRequest]) -> JSONResponse:
    print(data)
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
