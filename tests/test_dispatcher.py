from attr import dataclass
import logging

from orthanc_ext import event_dispatcher
from orthanc_ext.orthanc import OrthancApiHandler

orthanc = OrthancApiHandler()


@dataclass
class Event:
    change: orthanc.ChangeType = orthanc.ChangeType.UNKNOWN
    level: str = ""
    resource_id: str = ""


def capture(event):
    def capture_impl(change, level, resource_id, orthanc):
        event.change = change
        event.level = level
        event.resource_id = resource_id

    return capture_impl


def test_registered_callback_should_be_triggered_on_change_event():
    event = Event()
    
    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.ORTHANC_STARTED: capture(event)
    }, orthanc_module=orthanc)

    orthanc.on_change(orthanc.ChangeType.ORTHANC_STARTED, 'level', "resource-uuid")

    assert event.resource_id == "resource-uuid"
    assert event.level == 'level'


def test_no_registered_callbacks_should_be_reported_in_on_change_event(caplog):
    caplog.set_level(logging.INFO)

    event_dispatcher.register_event_handlers({}, orthanc_module=orthanc)
    orthanc.on_change(orthanc.ChangeType.ORTHANC_STARTED, 'level', "resource-uuid")

    assert "no handler registered for ORTHANC_STARTED" in caplog.text
