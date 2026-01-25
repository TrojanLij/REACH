"""Application-wide logging configuration helpers."""
from __future__ import annotations

from logging.config import dictConfig
from typing import Iterable
import logging
import os
import sys

DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_FILE_SIZE_BYTES = 5 * 1024 * 1024
DEFAULT_FILE_BACKUPS = 3


def _parse_csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _coerce_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    level_name = level.upper()
    numeric = logging.getLevelName(level_name)
    if isinstance(numeric, int):
        return numeric
    return logging.INFO


def setup_logging(
    *,
    level: str | int | None = None,
    logfile: str | None = None,
    trace_modules: Iterable[str] | None = None,
    quiet_modules: Iterable[str] | None = None,
) -> None:
    """
    Configure root logging for the app and all imported modules.

    Environment variables:
    - REACH_LOG_LEVEL (default: INFO)
    - REACH_LOG_FILE (optional file path)
    - REACH_LOG_TRACE (csv modules to force DEBUG)
    - REACH_LOG_QUIET (csv modules to force WARNING)
    """
    env_level = os.getenv("REACH_LOG_LEVEL")
    env_file = os.getenv("REACH_LOG_FILE")
    env_trace = _parse_csv(os.getenv("REACH_LOG_TRACE"))
    env_quiet = _parse_csv(os.getenv("REACH_LOG_QUIET"))

    effective_level = _coerce_level(level if level is not None else (env_level or "INFO"))
    log_path = logfile if logfile is not None else env_file
    trace = list(trace_modules or []) + env_trace
    quiet = list(quiet_modules or []) + env_quiet

    handlers: dict[str, dict[str, object]] = {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "standard",
        }
    }
    handler_names = ["console"]
    if log_path:
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_path,
            "maxBytes": DEFAULT_FILE_SIZE_BYTES,
            "backupCount": DEFAULT_FILE_BACKUPS,
            "formatter": "standard",
        }
        handler_names.append("file")

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": DEFAULT_LOG_FORMAT,
                    "datefmt": DEFAULT_DATE_FORMAT,
                }
            },
            "handlers": handlers,
            "root": {
                "level": effective_level,
                "handlers": handler_names,
            },
        }
    )

    logging.captureWarnings(True)

    for name in trace:
        logging.getLogger(name).setLevel(logging.DEBUG)
    for name in quiet:
        logging.getLogger(name).setLevel(logging.WARNING)
