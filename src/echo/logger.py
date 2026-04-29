import logging
import os
import sys

LOG_LEVELS_MAPPING = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
}

_DEFAULT_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

_logging_configured = False


def get_logger(
    name: str,
    log_level: str = "INFO",
    ignore_env_vars: bool = False,
    enable_stdout: bool = True,
) -> logging.Logger:
    """Configure logging (once) and return a named logger."""
    _configure_root_logging(
        log_level=log_level,
        ignore_env_vars=ignore_env_vars,
        enable_stdout=enable_stdout,
    )

    logger = logging.getLogger(name)
    logger.setLevel(_resolve_log_level(log_level, ignore_env_vars))
    logger.propagate = True

    return logger


def _configure_root_logging(
    *,
    log_level: str,
    ignore_env_vars: bool,
    enable_stdout: bool,
) -> None:
    global _logging_configured

    if _logging_configured:
        return

    level = _resolve_log_level(log_level, ignore_env_vars)
    root = logging.getLogger()
    root.setLevel(level)

    if enable_stdout and not _has_stream_handler(root):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(
            logging.Formatter(
                fmt=_DEFAULT_FORMAT,
                datefmt=_DEFAULT_DATEFMT,
            )
        )
        stream_handler.setLevel(level)
        root.addHandler(stream_handler)

    enable_otel = os.getenv("ENABLE_OTEL_LOGGING", "true").lower() == "true"
    if enable_otel:
        try:
            from opentelemetry.sdk._logs import LoggingHandler
        except ImportError:
            pass
        else:
            if not _has_otel_handler(root, LoggingHandler):
                root.addHandler(LoggingHandler(level=level))

    _logging_configured = True


def _resolve_log_level(log_level: str, ignore_env_vars: bool) -> int:
    if not ignore_env_vars:
        log_level = os.getenv("LOG_LEVEL", log_level)

    level = LOG_LEVELS_MAPPING.get(log_level.upper())
    if level is None:
        raise ValueError(f"Allowed log levels: {list(LOG_LEVELS_MAPPING.keys())}")
    return level


def _has_stream_handler(logger: logging.Logger) -> bool:
    return any(isinstance(h, logging.StreamHandler) for h in logger.handlers)


def _has_otel_handler(logger: logging.Logger, handler_cls: type) -> bool:
    return any(isinstance(h, handler_cls) for h in logger.handlers)
