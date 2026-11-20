import logging
import sys
import time
import uuid

import structlog
from fastapi import Request

def configure_logging():
    # Standard library logging configuration to pipe everything through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# Global logger instance
logger = structlog.get_logger()


async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    try:
        response = await call_next(request)
        latency = (time.perf_counter() - start_time) * 1000
        logger.info(
            "request_completed",
            path=request.url.path,
            method=request.method,
            status=response.status_code,
            latency_ms=round(latency, 2),
        )
        return response
    except Exception as exc:
        latency = (time.perf_counter() - start_time) * 1000
        logger.error(
            "request_failed",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            latency_ms=round(latency, 2),
        )
        raise
    finally:
        structlog.contextvars.clear_contextvars()


# Initialize logging on import
configure_logging()
