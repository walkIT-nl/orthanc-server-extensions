from dataclasses import dataclass

import nats

from orthanc_ext.scripts.event_publisher import convert_change_event_to_message


@dataclass
class NatsConfig:
    url: str
    stream_name: str = 'orthanc-events'
    subject = 'onchange'


async def create_stream(nats_config: NatsConfig, *_):
    nc = await nats.connect(nats_config.url)
    try:
        js = nc.jetstream()
        await js.add_stream(name=nats_config.stream_name, subjects=[nats_config.subject])
    finally:
        await nc.close()


async def publish_to_nats(nats_config: NatsConfig, evt, *_):
    nc = await nats.connect(nats_config.url)
    try:
        js = nc.jetstream()
        _, message = convert_change_event_to_message(evt)
        return await js.publish(nats_config.subject, message, stream=nats_config.stream_name)
    finally:
        await nc.close()
