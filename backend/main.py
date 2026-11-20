from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from app.api import chat, conversations, documents, health, memories, models, settings
from app.core.logging import logging_middleware
from app.core.limiter import limiter, RateLimitExceeded, _rate_limit_exceeded_handler
from app.services.runtime import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    rag_service.ensure_storage()
    yield



def create_app() -> FastAPI:
    app = FastAPI(title="LocalGPT API", lifespan=lifespan)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.middleware("http")(logging_middleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept"],
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
