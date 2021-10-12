import logging
import sys


def get_logger(name: str)-> logging.Logger:
    logger = logging.getLogger("App")

    # set level
    logger.setLevel(logging.INFO)

    # create a logging file handler
    fh = logging.FileHandler("logs.txt")
    fh.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(fh)

    # create a logging stream handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    sh.setFormatter(formatter)

    # add handler to logger object
    logger.addHandler(sh)

    return logger
