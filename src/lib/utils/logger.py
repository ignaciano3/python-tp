import logging
from random import choice
import string

import colorlog

pink = "\033[95m"


def create_logger(name=__name__, prefix=__name__, level=logging.INFO):
    random_name = "".join([pink + choice(string.ascii_letters) for _ in range(5)])
    logger = logging.getLogger(name + random_name)

    logger.setLevel(level)

    # Create a handler
    handler = colorlog.StreamHandler()

    # Define the format with colors
    formatter = colorlog.ColoredFormatter(
        f"{pink}%(asctime)s %(log_color)s {prefix} %(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "blue",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    # Set the formatter for the handler
    handler.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(handler)

    return logger
