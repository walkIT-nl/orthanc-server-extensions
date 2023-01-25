import time

import aio_pika
import httpx
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
def docker_rabbitmq():
    with containerlib.Context('rabbitmq:latest', {'5672/tcp': 55672}) as container:
        time.sleep(10)
        print(container.container.logs().decode('ascii'))
        yield container


async def create_queue(*_):
    connection = await aio_pika.connect_robust('amqp://guest:guest@127.0.0.1:55672/')
    try:
        queue_name = 'orthanc-events'
        channel = await connection.channel()
        await channel.declare_queue(queue_name, auto_delete=True)
    finally:
        await connection.close()


async def notify_rabbitmq(evt, _):
    connection = await aio_pika.connect_robust('amqp://guest:guest@127.0.0.1:55672/')
    try:
        queue_name = 'orthanc-events'
        channel = await connection.channel()
        _, message = convert_change_event_to_message(evt)
        await channel.default_exchange.publish(
            aio_pika.Message(body=message), routing_key=queue_name,
        )
    finally:
        connection.close()


async def get_first_message(*_):
    connection = await aio_pika.connect_robust('amqp://guest:guest@127.0.0.1:55672/')
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


def test_registered_callback_should_be_notify_change_event(docker_rabbitmq, orthanc):
    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.ORTHANC_STARTED: [create_queue],
        orthanc.ChangeType.STABLE_STUDY: [notify_rabbitmq, get_first_message],
    }, orthanc, httpx)

    orthanc.on_change(
        orthanc.ChangeType.ORTHANC_STARTED, orthanc.ResourceType.NONE, 'resource-uuid')

    _, msg = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')

    assert convert_message_to_change_event({}, msg).data == {
        'change_type': 9,
        'resource_id': 'resource-uuid',
        'resource_type': 1
    }
