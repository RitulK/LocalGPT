from contextlib import asynccontextmanager
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import structlog

import database
from app.api import chat, conversations, documents, health, memories, models, settings
from app.services.runtime import rag_service
from app.core.logging import logger

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from app.api import chat, conversations, documents, health, memories, models, settings
from app.services.runtime import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    rag_service.ensure_storage()
    yield


@asynccontextmanager
async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    # Bind request_id to the context for all logs in this request
    structlog.contextvars.bind_contextvars(request_id=request_id)

    try:
        response = await call_next(request)
        latency = (time.perf_counter() - start_time) * 1000
        logger.info("request_completed",
                    path=request.url.path,
                    method=request.method,
                    status=response.status_code,
                    latency_ms=round(latency, 2))
        return response
    except Exception as exc:
        latency = (time.perf_counter() - start_time) * 1000
        logger.error("request_failed",
                      path=request.url.path,
                      method=request.method,
                      error=str(exc),
                      latency_ms=round(latency, 2))
        raise exc
    finally:
        structlog.contextvars.clear_contextvars()


def create_app() -> FastAPI:
    app = FastAPI(title="LocalGPT API", lifespan=lifespan)

    app.middleware("http")(logging_middleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (
        health.router,
        models.router,
        conversations.router,
        documents.router,
        chat.router,
        settings.router,
        memories.router,
    ):
        app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
