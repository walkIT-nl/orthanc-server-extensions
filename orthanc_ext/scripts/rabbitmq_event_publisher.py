from dataclasses import dataclass

import aio_pika

from orthanc_ext.scripts.event_publisher import convert_change_event_to_message


@dataclass
class RabbitmqConfig:
    url: str
    queue_name: str = 'orthanc-events'


async def create_queue(rabbitmq_config: RabbitmqConfig, *_):
    connection = await aio_pika.connect_robust(rabbitmq_config.url)
    try:
        queue_name = rabbitmq_config.queue_name
        channel = await connection.channel()
        await channel.declare_queue(queue_name, auto_delete=True)
    finally:
        await connection.close()


async def publish_to_rabbitmq(rabbitmq_config: RabbitmqConfig, evt, *_):
    connection = await aio_pika.connect_robust(rabbitmq_config.url)
    try:
        queue_name = rabbitmq_config.queue_name
        channel = await connection.channel()
        _, message = convert_change_event_to_message(evt)
        await channel.default_exchange.publish(
            aio_pika.Message(body=message), routing_key=queue_name,
        )
    finally:
        await connection.close()
