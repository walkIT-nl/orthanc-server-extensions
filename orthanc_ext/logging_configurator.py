import logging
from enum import Enum


def configure_orthanc_log_format(default_level=logging.INFO):
    fmt = "%(levelname)s %(asctime)s %(filename)s:%(lineno)s] %(message)s"
    logging.basicConfig(format=fmt)
    logger = logging.getLogger()
    logger.setLevel(default_level)
    return fmt


class OrthancLevel(Enum):
    DEFAULT = ('default', 'WARNING')
    VERBOSE = ('verbose', 'INFO')
    TRACE = ('trace', 'DEBUG')

    def __init__(self, orthanc_level, python_level):
        self.orthanc_level = orthanc_level
        self.python_level = python_level


def configure_log_level(session, level: OrthancLevel):
    session.put('/tools/log-level-plugins', level.value)
