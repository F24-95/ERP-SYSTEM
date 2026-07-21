import json
import logging
import logging.handlers
import os
import sys
from contextvars import ContextVar
from datetime import datetime
from typing import Any

# Context variables for tracing
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="-")


class JSONFormatter(logging.Formatter):
    """Formatter that outputs JSON strings for logs, making them easily
    ingestable by log aggregators like ELK, Datadog, etc.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
            "request_id": request_id_ctx.get(),
            "user_id": user_id_ctx.get(),
        }
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


class ColorFormatter(logging.Formatter):
    """Console formatter with colors for local development."""

    GREY = "\x1b[38;20m"
    BLUE = "\x1b[34;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[41;97;1m"
    RESET = "\x1b[0m"

    LEVEL_COLORS = {
        logging.DEBUG: GREY,
        logging.INFO: BLUE,
        logging.WARNING: YELLOW,
        logging.ERROR: RED,
        logging.CRITICAL: BOLD_RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        usr_id = user_id_ctx.get()
        ctx = f"[req:{req_id} usr:{usr_id}]" if req_id != "-" else ""

        base_format = f"%(asctime)s [%(levelname)s] {ctx} %(name)s.%(funcName)s:%(lineno)d - %(message)s"
        base = logging.Formatter(base_format, datefmt="%Y-%m-%d %H:%M:%S").format(
            record,
        )

        if not sys.stdout.isatty():
            return base

        color = self.LEVEL_COLORS.get(record.levelno, self.RESET)
        return f"{color}{base}{self.RESET}"


def setup_logger(
    name: str = "school_erp",
    log_dir: str = "logs",
    level_str: str = "INFO",
    json_output: bool = False,
) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = getattr(logging, level_str.upper(), logging.INFO)
    logger.setLevel(level)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_output:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(ColorFormatter())
    logger.addHandler(console_handler)

    # File Handler
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    logger.propagate = False
    return logger


logger = setup_logger()


def get_logger(name: str = None) -> logging.Logger:
    if name:
        return setup_logger(name)
    return logger
