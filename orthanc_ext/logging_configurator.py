import enum
import logging
import sys


def python_logging(_, default_level=logging.INFO):
    """Configures python logging. Useful when Orthanc is using stderr and
    stdout handlers: offers more log levels and a better date format.
    """
    fmt = '%(levelname)s %(asctime)s %(filename)s:%(lineno)s] %(message)s'
    logging.basicConfig(format=fmt)
    logger = logging.getLogger()
    logger.setLevel(default_level)
    return fmt


def configure_orthanc_logging():

    def orthanc_logging(orthanc_module, default_level=logging.INFO):
        """Configures orthanc logging. Useful when orthanc is configured to write to a log file"""
        logger = logging.getLogger()
        logger.setLevel(default_level)
        logger.addHandler(logging.StreamHandler(sys.stderr))
        logger.addHandler(OrthancLogHandler(orthanc_module))

    return orthanc_logging


class OrthancLogHandler(logging.Handler):

    def __init__(self, orthanc_module):
        logging.Handler.__init__(self)
        self.orthanc_module = orthanc_module
        self.log_func_mapping = {
            logging.INFO: orthanc_module.LogInfo,
            logging.WARNING: orthanc_module.LogWarning,
            logging.ERROR: orthanc_module.LogError,
            logging.CRITICAL: orthanc_module.LogError,
        }

    def emit(self, record: logging.LogRecord) -> None:
        self.log_func_mapping.get(record.levelno, self.orthanc_module.LogInfo)(
            logging.Formatter(fmt='[%(filename)s:%(lineno)s] %(message)s').format(record))


class OrthancLevel(enum.Enum):
    DEFAULT = ('default', 'WARNING')
    VERBOSE = ('verbose', 'INFO')
    TRACE = ('trace', 'DEBUG')

    def __init__(self, orthanc_level, python_level):
        self.orthanc_level = orthanc_level
        self.python_level = python_level


def configure_log_level(client, level: OrthancLevel):
    client.put('/tools/log-level-plugins', level.value)
