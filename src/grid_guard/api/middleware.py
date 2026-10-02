"""Middleware and centralized exception handlers for Grid-Guard FastAPI service."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from grid_guard.api.schemas.common import ErrorResponse

logger = logging.getLogger("grid_guard.api")


async def request_id_and_logging_middleware(request: Request, call_next: Callable) -> Response:
    """Middleware attaching correlation request ID and recording operational latency."""
    # 1. Extract or generate Request ID
    req_id = request.headers.get("X-Request-ID")
    if not req_id:
        req_id = f"req-{uuid.uuid4().hex[:12]}"

    request.state.request_id = req_id
    start_time = time.perf_counter()

    # 2. Process request
    try:
        response: Response = await call_next(request)
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(
            f"[{req_id}] Unhandled failure on {request.method} {request.url.path} "
            f"({duration_ms:.2f}ms): {exc}",
            exc_info=True,
        )
        raise exc

    # 3. Attach Request ID header to response
    duration_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

    # 4. Safe operational log (omits sensitive consumption payloads)
    if not request.url.path.startswith("/health"):
        logger.info(
            f"[{req_id}] {request.method} {request.url.path} -> {response.status_code} "
            f"({duration_ms:.2f}ms)"
        )

    return response


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized custom exception handlers for uniform API error responses."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        error_payload = ErrorResponse(
            error_type="HTTPException",
            message=str(exc.detail),
            request_id=req_id,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=jsonable_encoder(error_payload.model_dump()),
            headers={"X-Request-ID": req_id} if req_id else {},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        safe_errors = jsonable_encoder(exc.errors())
        error_payload = ErrorResponse(
            error_type="ValidationError",
            message="Request schema validation failed.",
            details=safe_errors,
            request_id=req_id,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=jsonable_encoder(error_payload.model_dump()),
            headers={"X-Request-ID": req_id} if req_id else {},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = getattr(request.state, "request_id", None)
        logger.error(f"[{req_id}] Unhandled internal exception: {exc}", exc_info=True)
        error_payload = ErrorResponse(
            error_type=type(exc).__name__,
            message="An unexpected internal server error occurred.",
            request_id=req_id,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_payload.model_dump(),
            headers={"X-Request-ID": req_id} if req_id else {},
        )
