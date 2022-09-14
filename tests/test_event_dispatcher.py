import dataclasses
import logging

import httpx
import respx
import pytest

from orthanc_ext import event_dispatcher
from orthanc_ext.logging_configurator import python_logging
from orthanc_ext.orthanc import OrthancApiHandler

orthanc = OrthancApiHandler()


@dataclasses.dataclass
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
    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.STABLE_STUDY: capture(event)}, orthanc, httpx)
    orthanc.on_change(orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')
    assert event.resource_id == 'resource-uuid'
    assert event.resource_type == orthanc.ResourceType.STUDY
    assert event.orthanc is not None


def test_all_registered_callbacks_should_be_triggered_on_change_event():
    event1 = ChangeEvent()
    event2 = ChangeEvent()
    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.STABLE_STUDY: [capture(event1), capture(event2)]}, orthanc, httpx)
    orthanc.on_change(orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')
    assert event1.resource_id is not None
    assert event2.resource_id is not None


def test_no_registered_callbacks_should_be_reported_in_on_change_event(caplog):
    args = {}
    event_dispatcher.register_event_handlers(
        args, orthanc, httpx, logging_configuration=python_logging)
    caplog.set_level(logging.DEBUG)
    orthanc.on_change(orthanc.ChangeType.ORTHANC_STARTED, '', '')
    assert 'no handler registered for ORTHANC_STARTED' in caplog.text


@respx.mock
def test_shall_return_values_from_executed_handlers():
    system = respx.get('/system').respond(200, json={'Version': '1.9.0'})

    def get_system_info(_, client):
        return client.get('http://localhost:8042/system').json()

    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.ORTHANC_STARTED: get_system_info}, orthanc, httpx)
    (system_info, ) = orthanc.on_change(
        orthanc.ChangeType.ORTHANC_STARTED, orthanc.ResourceType.NONE, '')
    assert system.called
    assert system_info.get('Version') == '1.9.0'


def test_event_shall_have_human_readable_representation(caplog):
    caplog.set_level(logging.INFO)

    def log_event(evt, _):
        logging.info(evt)

    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.STABLE_STUDY: log_event}, orthanc, httpx)
    orthanc.on_change(orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'uuid')
    assert 'change_type=STABLE_STUDY' in caplog.text
    assert 'resource_type=STUDY' in caplog.text


def test_create_session_shall_pass_ssl_cert_if_ssl_is_enabled_and_report_issues():
    configured_orthanc = OrthancApiHandler(
        config={
            'SslEnabled': True,
            'SslCertificate': 'path-to-non-existing-file'
        })
    with pytest.raises(IOError, match='.*TLS CA.*invalid path: path-to-non-existing-file'):
        event_dispatcher.create_session(configured_orthanc)


def test_create_session_shall_not_raise_an_exception_for_a_non_existing_ssl_cert_if_ssl_is_disabled(
):
    configured_orthanc = OrthancApiHandler(
        config={
            'SslEnabled': False,
            'SslCertificate': 'path-to-non-existing-file'
        })

    client = event_dispatcher.create_session(configured_orthanc)

    assert_client_is_successfully_constructed(client)


def assert_client_is_successfully_constructed(client):
    assert client is not None
