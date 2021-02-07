import logging
import re

from orthanc_ext.logging_configurator import configure_orthanc_log_format


def test_setup_orthanc_log_format(caplog):
    fmt = configure_orthanc_log_format()
    # pytest overrides the log configuration; need to explicitly set the formatter to test it
    caplog.handler.setFormatter(logging.Formatter(fmt))
    logging.info("message")

    # level names and time format deviate from orthanc; timestamp includes date
    assert re.match(r'INFO 20\d\d-\d\d-\d\d .* test_logging_configurator.py:11] message', caplog.text)
