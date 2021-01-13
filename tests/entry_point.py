"""Test entry point script for Orthanc Python Plugin."""
from orthanc_ext import event_dispatcher

# provided by the plugin runtime.
import orthanc


def log_event(event):
    def log_event_impl(change, level, resource, orthanc):
        orthanc.LogWarning(f"orthanc '{event}' event handled!")

    return log_event_impl


event_dispatcher.register_event_handlers({
    orthanc.ChangeType.ORTHANC_STARTED: log_event("started"),
    orthanc.ChangeType.ORTHANC_STOPPED: log_event("stopped")
}, orthanc_module=orthanc)
