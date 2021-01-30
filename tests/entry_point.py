"""Test entry point script for Orthanc Python Plugin."""
import json

from orthanc_ext import event_dispatcher

# provided by the plugin runtime.
import orthanc


def log_event(param):
    def log_event_impl(event, orthanc):
        orthanc.LogWarning(f"orthanc '{event}' event handled with param {param}")

    return log_event_impl


def start_maintenance_cycle(event, orthanc):
    orthanc.LogWarning(f"do something special on {event}")


event_dispatcher.register_event_handlers({
    orthanc.ChangeType.ORTHANC_STARTED: [log_event("started"), start_maintenance_cycle],
    orthanc.ChangeType.ORTHANC_STOPPED: log_event("stopped")
}, orthanc_module=orthanc)
