"""Test entry point script for Orthanc Python Plugin."""
import json

from orthanc_ext import event_dispatcher

# provided by the plugin runtime.
import orthanc
import logging


def log_event(param):
    def log_event_impl(event, _):
        logging.warning(f"orthanc '{event}' event handled with param {param}")

    return log_event_impl


def start_maintenance_cycle(event, _):
    logging.warning(f"do something special on {event}")


def show_system_info(_, session):
    logging.warning("orthanc version retrieved: %s", session.get('/system').json().get('Version'))


event_dispatcher.register_event_handlers({
    orthanc.ChangeType.ORTHANC_STARTED: [log_event("started"), start_maintenance_cycle, show_system_info],
    orthanc.ChangeType.ORTHANC_STOPPED: log_event("stopped")
}, orthanc, event_dispatcher.create_session(orthanc))
