"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__
from app.api.routes.health import router as health_router
from app.api.routes.nid import router as nid_router
from app.core.config import get_settings
from app.core.exceptions import NIDExtractorError
from app.core.logging import configure_logging, duration_ms, reset_request_context, set_request_context
from app.models.responses import ErrorPayload, ErrorResponse
from app.ui.landing_page import build_landing_page_html

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", uuid4().hex)
    tokens = set_request_context(request_id)
    start = perf_counter()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info("request_complete path=%s method=%s status=%s duration_ms=%s", request.url.path, request.method, response.status_code, duration_ms(start))
        return response
    except Exception as exc:
        logger.exception("request_failed path=%s method=%s error=%s", request.url.path, request.method, exc.__class__.__name__)
        raise
    finally:
        reset_request_context(tokens)


@app.exception_handler(NIDExtractorError)
async def nid_extractor_error_handler(_: Request, exc: NIDExtractorError) -> JSONResponse:
    payload = ErrorResponse(error=ErrorPayload(code=exc.code, message=exc.message, details=exc.details))
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(by_alias=True))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorPayload(code="INTERNAL_SERVER_ERROR", message="The request could not be processed.", details=None)
    )
    return JSONResponse(status_code=400, content=payload.model_dump(by_alias=True))


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled application error: %s", exc)
    payload = ErrorResponse(error=ErrorPayload(code="INTERNAL_SERVER_ERROR", message="An internal server error occurred.", details=None))
    return JSONResponse(status_code=500, content=payload.model_dump(by_alias=True))


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    return HTMLResponse(content=build_landing_page_html(settings.app_name, __version__))


app.include_router(health_router)
app.include_router(nid_router)
