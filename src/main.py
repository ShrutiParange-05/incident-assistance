"""
FastAPI application entrypoint.

Wires together: structured logging, DB init, routers, a global
exception handler (the "Error Handler" box in the architecture
diagram — catches anything unhandled, logs it in structured form,
and returns a clean JSON error instead of a stack trace), and the
static dashboard.
"""
import logging
import time

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from src.database import get_db, init_db
from src.logging_config import configure_logging, log_extra
from src.routers import dashboard, incidents

configure_logging()
logger = logging.getLogger("incident_assistant")

app = FastAPI(
    title="AI-Powered Application Incident & Support Assistant",
    description=(
        "Ingests application errors, classifies them, retrieves relevant "
        "runbook context via RAG, and returns a GenAI-generated "
        "troubleshooting recommendation."
    ),
    version="1.0.0",
)

app.include_router(incidents.router)
app.include_router(dashboard.router)
app.mount("/static", StaticFiles(directory="src/static"), name="static")


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Application startup complete")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Structured access logging for every request, with latency."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        "HTTP request",
        extra=log_extra(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        ),
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches anything a route didn't handle itself. Logs full detail
    server-side (structured, with stack trace) but returns a generic
    message to the client — never leak internals in the response body.
    """
    logger.exception(
        "Unhandled exception",
        extra=log_extra(method=request.method, path=request.url.path),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. It has been logged for investigation."},
    )


@app.get("/health")
def health():
    """Liveness/readiness probe — also checks DB connectivity."""
    db_status = "ok"
    try:
        db_gen = get_db()
        db = next(db_gen)
        db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unreachable"
    return {"status": "ok", "database": db_status}


@app.get("/dashboard")
def dashboard_page():
    return FileResponse("src/static/dashboard.html")


@app.get("/")
def root():
    return {
        "message": "AI-Powered Application Incident & Support Assistant",
        "docs": "/docs",
        "dashboard": "/dashboard",
    }
