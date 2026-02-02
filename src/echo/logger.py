import logging
import os

LOG_LEVELS_MAPPING = {
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "WARN": logging.WARN,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
}


def configure_logger(
    name: str = "root",
    log_level: str = "INFO",
    ignore_env_vars: bool = False,
) -> logging.Logger:
    log = logging.getLogger(name)
    level = _get_log_level(log_level)

    if not ignore_env_vars:
        try:
            log_level_env = os.getenv("LOG_LEVEL", log_level)
            level = _get_log_level(log_level_env)
        except ValueError:
            pass

    return __logger_default_configuration(log, level)


def _get_log_level(log_level: str) -> int:
    level = LOG_LEVELS_MAPPING.get(log_level)

    if not level:
        raise ValueError(f"Allowed log levels: {LOG_LEVELS_MAPPING.keys()}")

    return level


def __logger_default_configuration(
    logger: logging.Logger,
    log_level: int = logging.INFO,
) -> logging.Logger:
    if log_level not in LOG_LEVELS_MAPPING.values():
        raise ValueError(f"Allowed log levels: {LOG_LEVELS_MAPPING.keys()}")

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(levelname)-8s %(message)s"))
    logger.setLevel(log_level)
    logger.addHandler(ch)
    logger.propagate = False
    return logger
