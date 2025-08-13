import json
import logging
import sys
from typing import Any, Dict

import structlog

from app.core.config import settings

# Global flag to prevent duplicate setup
_logging_configured = False


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


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter for standard Python logging records.
    Provides clean, colorized output suitable for development and debugging.
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()

        # Check if the message is already JSON (from structlog)
        try:
            parsed_message = json.loads(message)
            if isinstance(parsed_message, dict) and "timestamp" in parsed_message:
                # Format structlog JSON message for console
                timestamp = parsed_message.get("timestamp", "")
                level = parsed_message.get("level", "").upper()
                logger_name = parsed_message.get("logger", "")
                msg = parsed_message.get("event", parsed_message.get("message", ""))

                # Extract additional fields
                extra_fields = {
                    k: v
                    for k, v in parsed_message.items()
                    if k not in ["timestamp", "level", "logger", "event", "message"]
                }

                formatted_msg = self._format_message(
                    timestamp, level, logger_name, msg, extra_fields
                )
                return formatted_msg
        except (json.JSONDecodeError, ValueError):
            pass

        # Format regular log record
        timestamp = self.formatTime(record)
        level = record.levelname
        logger_name = record.name
        msg = message

        # Collect extra fields
        extra_fields = {}
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
                extra_fields[key] = value

        formatted_msg = self._format_message(
            timestamp, level, logger_name, msg, extra_fields
        )

        # Add exception information if present
        if record.exc_info:
            formatted_msg += "\n" + self.formatException(record.exc_info)

        return formatted_msg

    def _format_message(
        self,
        timestamp: str,
        level: str,
        logger_name: str,
        message: str,
        extra_fields: Dict[str, Any] = None,
    ) -> str:
        """Format the log message components into a readable string."""
        # Truncate timestamp to remove microseconds for cleaner output
        if "T" in timestamp and "." in timestamp:
            timestamp = timestamp.split(".")[0] + "Z"

        # Apply colors if enabled
        if self.use_colors:
            level_color = self.COLORS.get(level, "")
            level_str = f"{level_color}{self.BOLD}{level:<8}{self.RESET}"
        else:
            level_str = f"{level:<8}"

        # Format the base message
        formatted = f"{timestamp} {level_str} [{logger_name}] {message}"

        # Add extra fields if present
        if extra_fields:
            extra_str = " | ".join([f"{k}={v}" for k, v in extra_fields.items()])
            formatted += f" | {extra_str}"

        return formatted

    def formatTime(self, record: logging.LogRecord, datefmt: str = None) -> str:
        """Format timestamp in ISO format."""
        import datetime

        dt = datetime.datetime.fromtimestamp(record.created, tz=datetime.timezone.utc)
        return dt.isoformat()


def setup_logging():
    """
    Set up structured, configurable logging for the application.
    Output format depends on settings.log_format configuration.
    """
    global _logging_configured

    # Prevent duplicate configuration
    if _logging_configured:
        return

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_format = getattr(settings, "log_format", "json").lower()  # Default to JSON
    use_colors = getattr(
        settings, "log_use_colors", True
    )  # Default to colorized output

    # Clear any existing handlers to prevent duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Configure structlog based on format choice
    if log_format == "console":
        # Console-friendly configuration
        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
        ]

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                *shared_processors,
                # Use JSONRenderer even for console mode so ConsoleFormatter can parse it
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Use console formatter
        formatter = ConsoleFormatter(use_colors=use_colors)

    else:
        # JSON configuration (default)
        shared_processors = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.dict_tracebacks,
        ]

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                *shared_processors,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Use JSON formatter
        formatter = JSONFormatter()

    # Configure the root logger
    root_logger.setLevel(log_level)

    # Create and add a single StreamHandler with chosen formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Configure specific loggers
    loggers_to_configure = ["uvicorn.access", "uvicorn", "fastapi", "google_adk"]

    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
        logger.propagate = True

    # Optionally disable uvicorn access logs (uncomment if needed)
    # logging.getLogger("uvicorn.access").disabled = True

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
        A structured logger instance that outputs in the configured format.
    """
    if name is None:
        import inspect

        frame = inspect.currentframe().f_back
        name = frame.f_globals.get("__name__", "unknown")

    return structlog.get_logger(name)
