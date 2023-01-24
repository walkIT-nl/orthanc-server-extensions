import time

import aio_pika
import pytest
from dockercontext import container as containerlib


@pytest.fixture(scope='session')
def docker_rabbitmq():
    with containerlib.Context('rabbitmq:latest', {'5672/tcp': 55672}) as container:
        time.sleep(10)
        print(container.container.logs().decode('ascii'))
        yield container


@pytest.mark.asyncio
async def test_create_queue(docker_rabbitmq):
    connection = await aio_pika.connect_robust('amqp://guest:guest@127.0.0.1:55672/')
    try:
        queue_name = 'orthanc-events'
        channel = await connection.channel()
        queue = await channel.declare_queue(queue_name, auto_delete=True)

        await channel.default_exchange.publish(
            aio_pika.Message(body=f'Hello {queue_name}'.encode()), routing_key=queue_name,
        )

        messages = []
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    messages.append(message.body.decode())
                    break

        assert 'Hello orthanc-events' == messages[0]
    finally:
        await connection.close()
