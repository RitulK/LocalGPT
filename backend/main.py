from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import database
from app.api import chat, conversations, documents, health, memories, models, obsidian, settings
from app.core.logging import logging_middleware
from app.core.limiter import limiter, RateLimitExceeded, _rate_limit_exceeded_handler
from app.services.runtime import rag_service
from app.services.document_service import reindex_pending_documents


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    rag_service.ensure_storage()
    recovery_task = asyncio.create_task(reindex_pending_documents())
    yield
    recovery_task.cancel()



def create_app() -> FastAPI:
    app = FastAPI(title="Buddyai API", lifespan=lifespan)
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
        obsidian.router,
    ):
        app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
