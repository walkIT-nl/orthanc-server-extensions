import asyncio
import dataclasses
import logging
import time
from functools import partial

import httpx
import respx
import pytest

from orthanc_ext import event_dispatcher
from orthanc_ext.http_utilities import create_internal_client, ClientType
from orthanc_ext.logging_configurator import python_logging
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.python_utilities import pipeline

orthanc = OrthancApiHandler()


@pytest.fixture
def async_client():
    return create_internal_client('https://localhost:8042', '', client_type=ClientType.ASYNC)


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

        return event

    return capture_impl


async def async_func(return_value, evt, session):
    assert evt is not None
    assert session is not None
    return return_value


async def async_fail(*_):
    raise Exception('failed')


async def async_get(_, session):
    return await session.get('http://localhost:0/')


async def async_sleep(*_):
    await asyncio.sleep(0.5)
    return 42


def test_registered_callback_should_be_triggered_on_change_event():
    event = ChangeEvent()
    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.STABLE_STUDY: capture(event)}, orthanc, httpx)
    sync_result = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')
    assert sync_result[0].resource_id == 'resource-uuid'
    assert sync_result[0].resource_type == orthanc.ResourceType.STUDY
    assert sync_result[0].orthanc is not None


@dataclasses.dataclass
class StableStudyEvent:
    resource_id: str
    StudyInstanceUid: str = None


def embellish(evt, client) -> StableStudyEvent:
    study = client.get(f'http://localhost/studies/{evt.resource_id}').json()
    return StableStudyEvent(evt.resource_id, study.get('StudyInstanceUid'))


def publish(evt: StableStudyEvent, client):
    client.post('http://localhost/publish', json=dataclasses.asdict(evt))
    return evt


@respx.mock
def test_pipeline_should_run_all_functions_to_completion_passing_results_to_the_next_function():
    respx.get('http://localhost/studies/resource-uuid').respond(
        200, json={'StudyInstanceUid': '1.2.3'})
    respx.post('http://localhost/publish').respond(200)

    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.STABLE_STUDY: pipeline(embellish, publish)}, orthanc, httpx)
    publication_response = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')

    assert publication_response == [
        StableStudyEvent(resource_id='resource-uuid', StudyInstanceUid='1.2.3')
    ]


def test_registered_async_callback_should_be_run_to_completion_on_change_event(async_client):
    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.STABLE_STUDY: partial(async_func, 42)}, orthanc, httpx, async_client)
    async_result = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')
    assert async_result == [42]


def test_multiple_registered_async_callbacks_should_be_run_to_completion_on_change_event(
        async_client):
    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.STABLE_STUDY: [partial(async_func, 42),
                                           partial(async_func, 41)]}, orthanc, httpx, async_client)
    async_result = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')
    assert async_result == [42, 41]


def test_all_async_callbacks_should_be_run_to_completion_on_change_event_if_one_or_more_fail(
        caplog, async_client):
    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.STABLE_STUDY:
            [async_fail, async_get,
             partial(async_func, 42),
             partial(async_func, 41)]
    }, orthanc, httpx, async_client)
    async_result = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')

    exception = async_result[0]
    http_exception = async_result[1]

    assert async_result == [exception, http_exception, 42, 41]
    assert exception.args == ('failed', )
    assert type(exception) == Exception

    assert 'async_fail' in caplog.messages[0]
    assert "Exception('failed')" in caplog.messages[0]

    assert "ConnectError('All connection attempts failed')" in caplog.messages[1]


def test_async_callbacks_should_be_run_concurrently_on_change_event(async_client):
    awaitables = []
    start = time.perf_counter()
    for i in range(0, 10):
        awaitables.append(async_sleep)
    event_dispatcher.register_event_handlers(
        {orthanc.ChangeType.STABLE_STUDY: awaitables}, orthanc, httpx, async_client)
    async_result = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')
    assert async_result == [42, 42, 42, 42, 42, 42, 42, 42, 42, 42]
    assert time.perf_counter() - start < 1


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
