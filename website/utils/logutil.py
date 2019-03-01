import os
import logging

LOG_FORMAT = '{asctime} | {levelname:.1} | {name:^24} |  {message}'

LOG_LEVEL = os.environ.get('CST_LOG_LEVEL') or logging.INFO


def get_logger(name: str) -> logging.Logger:
    """Creates logger with given name"""
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = False
    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT, logging.Formatter.default_time_format, style='{')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def configure():
    """Configures global logging settings"""
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT,
                        style='{', datefmt=logging.Formatter.default_time_format)

    tweak()


def tweak():
    """Tweak default loggers here"""
    logging.getLogger('urllib3.connectionpool').disabled = True


def format_exception(exc: Exception) -> str:
    """Formats exception for log entries"""
    return f'| {exc.__class__.__name__}: {exc}'
