import json
import logging
import sys
from typing import Any, Dict

import structlog

from app.core.config import get_settings

# Global flag to prevent duplicate setup
_logging_configured = False
settings = get_settings()


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for standard Python logging records.
    This ensures that all log records, including those from Uvicorn and other libraries,
    are formatted as JSON. Handles both structlog-generated JSON and regular log messages.
    """

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()

        # Check if the message is already JSON (from structlog)
        try:
            # Try to parse the message as JSON
            parsed_message = json.loads(message)

            # If it's valid JSON and looks like a structlog message, use it directly
            if isinstance(parsed_message, dict) and "timestamp" in parsed_message:
                return message
            else:
                # It's JSON but not from structlog, treat as regular message
                raise ValueError("Not a structlog message")

        except (json.JSONDecodeError, ValueError):
            # Not JSON or not a structlog message, format as regular log entry
            log_entry: Dict[str, Any] = {
                "timestamp": self.formatTime(record),
                "level": record.levelname.lower(),
                "logger": record.name,
                "message": message,
            }

            # Add exception information if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)

            # Add extra fields from the record
            for key, value in record.__dict__.items():
                if key not in (
                    "name",
                    "msg",
                    "args",
                    "levelname",
                    "levelno",
                    "pathname",
                    "filename",
                    "module",
                    "lineno",
                    "funcName",
                    "created",
                    "msecs",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "processName",
                    "process",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                ):
                    log_entry[key] = value

            return json.dumps(log_entry, default=str, ensure_ascii=False)

    def formatTime(self, record: logging.LogRecord, datefmt: str = None) -> str:
        """Format timestamp in ISO format."""
        import datetime

        dt = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)
        return dt.isoformat()


def setup_logging():
    """
    Set up structured, configurable logging for the application.
    All logs will be output in JSON format.
    """
    global _logging_configured

    # Prevent duplicate configuration
    if _logging_configured:
        return

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Clear any existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # A list of processors that will be applied to all log records from structlog.
    shared_processors = [
        # This processor must be first to add context from structlog.contextvars.
        structlog.contextvars.merge_contextvars,
        # Add logger-specific context.
        structlog.stdlib.add_logger_name,
        # Add the log level to the record.
        structlog.stdlib.add_log_level,
        # Add a timestamp to the record.
        structlog.processors.TimeStamper(fmt="iso"),
        # Perform key-value formatting.
        structlog.processors.dict_tracebacks,
    ]

    # Configure structlog
    structlog.configure(
        processors=[
            # This processor is used to filter log records by level.
            structlog.stdlib.filter_by_level,
            *shared_processors,
            # This processor must be last to render the log record.
            structlog.processors.JSONRenderer(),
        ],
        # The context class is used to store thread-local context.
        context_class=dict,
        # The logger factory is used to create standard Python loggers.
        logger_factory=structlog.stdlib.LoggerFactory(),
        # This wrapper class is used to make standard loggers compatible with structlog.
        wrapper_class=structlog.stdlib.BoundLogger,
        # Cache the logger on first use.
        cache_logger_on_first_use=True,
    )

    # Configure the root logger with JSON formatting
    root_logger.setLevel(log_level)

    # Create and add a single StreamHandler with JSON formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    # Use the custom JSON formatter for all standard logging records
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)

    # Configure specific loggers to use JSON format
    # Uvicorn access logs
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(log_level)
    uvicorn_access_logger.propagate = (
        True  # Let it propagate to root logger for JSON formatting
    )

    # Uvicorn main logger
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(log_level)
    uvicorn_logger.propagate = True

    # FastAPI logger
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(log_level)
    fastapi_logger.propagate = True

    # google adk logger
    google_adk_logger = logging.getLogger("google_adk")
    google_adk_logger.setLevel(log_level)
    google_adk_logger.propagate = True

    # If you want to completely disable certain loggers, you can do so:
    logging.getLogger("uvicorn.access").disabled = True

    # Mark as configured
    _logging_configured = True


def reset_logging():
    """Reset logging configuration - useful for tests."""
    global _logging_configured

    # Clear all handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Reset structlog
    structlog.reset_defaults()

    # Reset flag
    _logging_configured = False


def get_logger(name: str = None):
    """
    Get a structured logger instance.

    Args:
        name: Logger name. If None, uses the caller's module name.

    Returns:
        A structured logger instance that outputs JSON.
    """
    if name is None:
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "unknown")

    return structlog.get_logger(name)
