"""Worker process lifecycle helpers."""

from __future__ import annotations

import logging
import signal
import threading
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

WorkerLoop = Callable[[threading.Event], None]


@dataclass(frozen=True)
class WorkerConfig:
    name: str
    poll_interval_seconds: float = 1.0


class WorkerRunner:
    """Run a background worker loop with graceful shutdown on SIGTERM/SIGINT."""

    def __init__(self, config: WorkerConfig, loop: WorkerLoop | None = None) -> None:
        self.config = config
        self._loop = loop or self._default_loop
        self._stop = threading.Event()

    def _default_loop(self, stop: threading.Event) -> None:
        while not stop.wait(self.config.poll_interval_seconds):
            logger.debug("worker %s heartbeat", self.config.name)

    def _handle_signal(self, signum: int, _frame) -> None:
        logger.info("worker %s received signal %s; shutting down", self.config.name, signum)
        self._stop.set()

    def run(self) -> None:
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

        logger.info("worker %s starting", self.config.name)
        try:
            self._loop(self._stop)
        finally:
            logger.info("worker %s stopped", self.config.name)
