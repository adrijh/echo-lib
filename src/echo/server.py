import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

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


@app.get("/health", tags=["health"])
def healthcheck() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={"status": "ok"}
    )


@app.get("/sessions")
async def list_sessions() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=[],
    )


@app.post("/sessions")
async def start_session() -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=[],
    )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        # data = await websocket.receive_text()
        rooms = db.get_rooms()
        await websocket.send_json({"rooms": rooms})
        await asyncio.sleep(WS_REFRESH_TIME_SECONDS)
