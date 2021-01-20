import logging
import re
from time import sleep

import requests
from attr import dataclass

from orthanc_ext import event_dispatcher
from orthanc_ext.orthanc import OrthancApiHandler

orthanc = OrthancApiHandler()


@dataclass
class ChangeEvent:
    change: orthanc.ChangeType = orthanc.ChangeType.UNKNOWN
    resource_type: int = orthanc.ResourceType.NONE
    resource_id: str = None
    orthanc = None


def capture(event):
    def capture_impl(incoming_event, local_orthanc):
        event.change = incoming_event.change_type
        event.resource_type = incoming_event.resource_type
        event.resource_id = incoming_event.resource_id
        event.orthanc = local_orthanc

    return capture_impl


def test_registered_callback_should_be_triggered_on_change_event():
    event = ChangeEvent()

    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.STABLE_STUDY: capture(event)
    }, orthanc_module=orthanc)

    orthanc.on_change(orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, "resource-uuid")

    assert event.resource_id == "resource-uuid"
    assert event.resource_type == orthanc.ResourceType.STUDY
    assert event.orthanc is not None


def test_all_registered_callbacks_should_be_triggered_on_change_event():
    event1 = ChangeEvent()
    event2 = ChangeEvent()

    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.STABLE_STUDY: [capture(event1), capture(event2)]
    }, orthanc_module=orthanc)

    orthanc.on_change(orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, "resource-uuid")

    assert event1.resource_id is not None
    assert event2.resource_id is not None


def test_no_registered_callbacks_should_be_reported_in_on_change_event(caplog):
    caplog.set_level(logging.INFO)

    event_dispatcher.register_event_handlers({}, orthanc_module=orthanc)
    orthanc.on_change(orthanc.ChangeType.ORTHANC_STARTED, '', '')

    assert "no handler registered for ORTHANC_STARTED" in caplog.text
