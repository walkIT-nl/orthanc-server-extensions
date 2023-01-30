from functools import partial

import httpx
import nats
import pytest
from dockercontext import container as containerlib

from orthanc_ext import event_dispatcher
from orthanc_ext.http_utilities import create_internal_client, ClientType
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.scripts.event_publisher import convert_message_to_change_event

from orthanc_ext.scripts.nats_event_publisher import publish_to_nats, create_stream, NatsConfig


@pytest.fixture
def nats_config():
    return NatsConfig('localhost:54222')


@pytest.fixture(scope='session')
def orthanc():
    yield OrthancApiHandler()


@pytest.fixture(scope='session')
def nats_server():
    with containerlib.Context('nats:latest', {'4222/tcp': 54222}, '-js') as container:
        yield container


@pytest.fixture
def async_client():
    return create_internal_client('https://localhost:8042', '', client_type=ClientType.ASYNC)


async def get_first_message(nats_config, *_):
    nc = await nats.connect(nats_config.url)
    try:
        js = nc.jetstream()
        sub = await js.pull_subscribe(
            nats_config.subject, 'orthanc-1', stream=nats_config.stream_name)

        msg = await sub.fetch(1, timeout=10)
        return msg[0]
    finally:
        await nc.close()


def test_registered_callback_should_be_notify_change_event(
        nats_server, orthanc, async_client, nats_config):
    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.ORTHANC_STARTED: [partial(create_stream, nats_config)],
        orthanc.ChangeType.STABLE_STUDY:
            [partial(publish_to_nats, nats_config),
             partial(get_first_message, nats_config)],
    }, orthanc, httpx, async_client)

    orthanc.on_change(
        orthanc.ChangeType.ORTHANC_STARTED, orthanc.ResourceType.NONE, 'resource-uuid')

    ack, message = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')
    event = convert_message_to_change_event({}, data=message.data)

    assert ack == nats.js.api.PubAck(stream='orthanc-events', seq=1, domain=None, duplicate=None)
    assert message.subject == 'onchange'
    assert event.data == {'change_type': 9, 'resource_type': 1, 'resource_id': 'resource-uuid'}
