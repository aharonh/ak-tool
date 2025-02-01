import logging
import sys


def setup_logger(name: str = "ak", debug: bool = False) -> logging.Logger:
    """Create and return a logger with either DEBUG or INFO level."""

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if not logger.handlers:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(logging.DEBUG if debug else logging.INFO)
        fmt = logging.Formatter(
            "[%(levelname)s] [%(name)s] %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        ch.setFormatter(fmt)
        logger.addHandler(ch)

    return logger
