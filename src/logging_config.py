"""
Structured (JSON-line) logging setup.

Every log record is emitted as a single-line JSON object so it can be
shipped to and queried by any log aggregator (ELK, Loki, CloudWatch,
Datadog, etc.) without a custom parser. This is what the Incident
Analyzer reads from when it scans for errors.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone

from src.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """Renders each LogRecord as one JSON line with consistent keys."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Allow callers to attach structured extras, e.g.
        # logger.error("db failed", extra={"extra_fields": {"service": "payment-api"}})
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            payload.update(extra_fields)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_logging() -> logging.Logger:
    """Configure root logging once. Safe to call multiple times (idempotent)."""
    os.makedirs(os.path.dirname(settings.log_file) or ".", exist_ok=True)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return logging.getLogger("incident_assistant")

    root_logger.setLevel(settings.log_level)

    formatter = JSONFormatter()

    file_handler = logging.FileHandler(settings.log_file)
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    return logging.getLogger("incident_assistant")


def log_extra(**fields) -> dict:
    """Helper: logger.error(msg, extra=log_extra(service="x", error_code=500))"""
    return {"extra_fields": fields}
