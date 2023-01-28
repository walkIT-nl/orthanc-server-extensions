import os

import aio_pika

from orthanc_ext.scripts.event_publisher import convert_change_event_to_message


async def create_queue(*_):
    connection = await aio_pika.connect_robust(get_rabbitmq_url())
    try:
        queue_name = 'orthanc-events'
        channel = await connection.channel()
        await channel.declare_queue(queue_name, auto_delete=True)
    finally:
        await connection.close()


def get_rabbitmq_url():
    return os.getenv('RABBITMQ_URL', 'amqp://guest:guest@127.0.0.1:55672/')


async def publish_to_rabbitmq(evt, *_):
    connection = await aio_pika.connect_robust(get_rabbitmq_url())
    try:
        queue_name = 'orthanc-events'
        channel = await connection.channel()
        _, message = convert_change_event_to_message(evt)
        await channel.default_exchange.publish(
            aio_pika.Message(body=message), routing_key=queue_name,
        )
    finally:
        await connection.close()
