import logging
import sys


def configure_logging() -> None:
    """Configure standard structured-enough logging without secrets."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

