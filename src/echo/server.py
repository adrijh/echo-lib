from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from echo.worker.queue import QueueWorker
from echo.utils import duckdb

@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    worker = await QueueWorker.build()
    await worker.start()
    yield
    await worker.stop()


app = FastAPI(lifespan=lifespan)


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
