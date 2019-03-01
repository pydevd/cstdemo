import pathlib
from multiprocessing import Queue

from utils import logutil

LOG = logutil.get_logger(__name__)


class Worker:

    def __init__(self):
        self.tasks = None

    def __call__(self, tasks_queue: Queue):
        self.tasks = tasks_queue
        LOG.info("worker started.")
        while True:
            task = self.tasks.get()
            LOG.debug("received task: %s", task)
            if task == 'stop':
                LOG.info("worker terminated.")
                break
