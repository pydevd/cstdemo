import contextlib
import logging
import time
import uuid

from website.utils import logutil

LOG = logutil.get_logger(__name__)


class PostMessage:
    """Helper class.

    Instance of this class returned by context manager. Main purpose is to
    include to log information, that can be extracted in context manager code
    block during runtime. For example:

    with log_time('hitting database...') as pm:
      rows = db.select('SELECT...')
      pm.message = 'fetched {} rows'.format(len(rows))
    """

    def __init__(self):
        self.message = ''


@contextlib.contextmanager
def log_time(message: str = '', level: int = logging.DEBUG):
    """Measures execution time of context manager's code block and writes
    execution time in seconds to the log after passed message."""
    start_time = time.monotonic()
    pm = PostMessage()
    try:
        yield pm
    finally:
        msg = ' '.join((message, pm.message)) if pm.message else message
        execution_time = time.monotonic() - start_time
        LOG.log(level, '%s (%.6fs)', msg, execution_time)


def unique_filename(extension: str) -> str:
    """Generates unique file name using uuid and provided extension"""
    uuid_str = str(uuid.uuid4())
    return '.'.join((uuid_str, extension))
