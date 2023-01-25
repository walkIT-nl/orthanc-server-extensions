import httpx
import nats
import pytest
from dockercontext import container as containerlib

from orthanc_ext import event_dispatcher
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.scripts.event_publisher import convert_change_event_to_message, \
    convert_message_to_change_event


@pytest.fixture(scope='session')
def orthanc():
    yield OrthancApiHandler()


@pytest.fixture(scope='session')
def nats_server():
    with containerlib.Context('nats:latest', {'4222/tcp': 54222}, '-js') as container:
        yield container


async def create_stream(evt, _):
    nc = await nats.connect('localhost:54222')
    try:
        js = nc.jetstream()
        await js.add_stream(name='orthanc-events', subjects=['onchange'])
    finally:
        await nc.close()


async def notify_nats(evt, _):
    nc = await nats.connect('localhost:54222')
    try:
        js = nc.jetstream()
        _, message = convert_change_event_to_message(evt)
        ack = await js.publish('onchange', message, stream='orthanc-events')
    finally:
        await nc.close()
    return ack


async def get_first_message(evt, _):
    nc = await nats.connect('localhost:54222')
    try:
        js = nc.jetstream()
        sub = await js.pull_subscribe('onchange', 'orthanc-1', stream='orthanc-events')

        msg = await sub.fetch(1, timeout=10)
        return msg[0]
    finally:
        await nc.close()


def test_registered_callback_should_be_notify_change_event(nats_server, orthanc):
    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.STABLE_STUDY: [notify_nats, get_first_message],
        orthanc.ChangeType.ORTHANC_STARTED: [create_stream]
    }, orthanc, httpx)

    orthanc.on_change(
        orthanc.ChangeType.ORTHANC_STARTED, orthanc.ResourceType.NONE, 'resource-uuid')

    ack, message = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')
    event = convert_message_to_change_event({}, data=message.data)

    assert ack == nats.js.api.PubAck(stream='orthanc-events', seq=1, domain=None, duplicate=None)
    assert message.subject == 'onchange'
    assert event.data == {'change_type': 9, 'resource_type': 1, 'resource_id': 'resource-uuid'}
