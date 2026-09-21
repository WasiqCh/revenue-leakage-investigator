"""Placeholder worker entrypoint.

TICKET-002 needs the worker container to stay up so the stack reaches
all-healthy. It does no work yet: TICKET-032 replaces this with the real loop
that claims jobs from the Postgres queue with ``FOR UPDATE SKIP LOCKED``
(see ADR-005).
"""

import logging
import signal
import time

logger = logging.getLogger(__name__)

POLL_SECONDS = 5.0
_running = True


def _handle_stop(signum: int, _frame: object) -> None:
    """Stop the loop cleanly so the container shuts down on SIGTERM."""
    global _running
    logger.info("worker received signal %s, shutting down", signum)
    _running = False


def run() -> None:
    """Idle until told to stop. The real job loop arrives in TICKET-032."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)
    logger.info("worker idle, polling every %.1fs", POLL_SECONDS)
    while _running:
        time.sleep(POLL_SECONDS)
    logger.info("worker stopped")


if __name__ == "__main__":
    run()
