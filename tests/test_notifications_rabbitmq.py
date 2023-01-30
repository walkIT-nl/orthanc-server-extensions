import time
from functools import partial

import aio_pika
import httpx
import pytest
from dockercontext import container as containerlib

from orthanc_ext import event_dispatcher
from orthanc_ext.http_utilities import create_internal_client, ClientType
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.scripts.event_publisher import convert_message_to_change_event
from orthanc_ext.scripts.rabbitmq_event_publisher import create_queue, publish_to_rabbitmq, \
    RabbitmqConfig


@pytest.fixture()
def rabbitmq_config():
    return RabbitmqConfig('amqp://guest:guest@127.0.0.1:55672/')


@pytest.fixture(scope='session')
def orthanc():
    yield OrthancApiHandler()


@pytest.fixture
def async_client():
    return create_internal_client('https://localhost:8042', '', client_type=ClientType.SYNC)


@pytest.fixture(scope='session')
def docker_rabbitmq():
    with containerlib.Context('rabbitmq:latest', {'5672/tcp': 55672}) as container:
        time.sleep(10)
        print(container.container.logs().decode('ascii'))
        yield container


async def get_first_message(rabbitmq_config, *_):
    connection = await aio_pika.connect_robust(rabbitmq_config.url)
    try:
        queue_name = 'orthanc-events'
        channel = await connection.channel()
        queue = await channel.get_queue(queue_name, ensure=False)
        messages = []
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    messages.append(message.body)
                    break

        return messages[0]
    finally:
        await connection.close()


def test_registered_callback_should_be_notify_change_event(
        docker_rabbitmq, orthanc, async_client, rabbitmq_config):
    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.ORTHANC_STARTED: [partial(create_queue, rabbitmq_config)],
        orthanc.ChangeType.STABLE_STUDY: [
            partial(publish_to_rabbitmq, rabbitmq_config),
            partial(get_first_message, rabbitmq_config)
        ],
    }, orthanc, httpx, async_client)

    orthanc.on_change(
        orthanc.ChangeType.ORTHANC_STARTED, orthanc.ResourceType.NONE, 'resource-uuid')

    _, msg = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')

    assert convert_message_to_change_event({}, msg).data == {
        'change_type': 9,
        'resource_id': 'resource-uuid',
        'resource_type': 1
    }
