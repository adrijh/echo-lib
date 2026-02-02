from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from echo.logger import configure_logger
from echo.worker.queue import QueueWorker, RabbitQueue

log = configure_logger(__name__)

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
def healthcheck():
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
