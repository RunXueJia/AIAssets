import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from contextvars import ContextVar

from fastapi import Request, Response

logger = logging.getLogger("hours24")
_factory_installed = False
trace_id_var: ContextVar[str] = ContextVar("trace_id", default="-")


def configure_logging() -> None:
    global _factory_installed
    if not _factory_installed:
        old_factory = logging.getLogRecordFactory()

        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.trace_id = trace_id_var.get()
            return record

        logging.setLogRecordFactory(record_factory)
        _factory_installed = True

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s trace_id=%(trace_id)s %(message)s",
    )


async def trace_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    token = trace_id_var.set(trace_id)
    request.state.trace_id = trace_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        response.headers["X-Trace-Id"] = trace_id
        logger.info(
            "%s %s status=%s elapsed_ms=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response
    finally:
        trace_id_var.reset(token)
