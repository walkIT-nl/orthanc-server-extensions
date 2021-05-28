import logging
import re

from orthanc_ext.logging_configurator import python_logging
from orthanc_ext.orthanc import OrthancApiHandler


def test_setup_orthanc_log_format(caplog):
    fmt = python_logging(OrthancApiHandler())
    # pytest overrides the log configuration; need to explicitly set the formatter to test it
    caplog.handler.setFormatter(logging.Formatter(fmt))
    logging.info('message')
    # level names and time format deviate from orthanc; timestamp includes date
    assert re.match(
        r'INFO 20\d\d-\d\d-\d\d .* test_logging_configurator.py:\d\d] message', caplog.text)
