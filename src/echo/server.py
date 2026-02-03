import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.websocket("/")
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

# @app.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket) -> None:
#     await websocket.accept()
#     log.info("WebSocket client connected")
#
#     try:
#         while True:
#             rooms = db.get_rooms()
#             await websocket.send_json({"rooms": [room.model_dump_json() for room in rooms]})
#             await asyncio.sleep(WS_REFRESH_TIME_SECONDS)
#     except WebSocketDisconnect:
#         log.info("WebSocket client disconnected normally")
#     except Exception as e:
#         log.error(f"WebSocket error: {e}")
#     finally:
#         log.info("WebSocket connection closed")
#         try:
#             await websocket.close()
#         except Exception as e:
#             log.error(f"Error closing websocket connection {e}")
