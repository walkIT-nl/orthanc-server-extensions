import os

import nats

from orthanc_ext.scripts.event_publisher import convert_change_event_to_message


async def create_stream(*_):
    nc = await nats.connect(get_nats_url())
    try:
        js = nc.jetstream()
        await js.add_stream(name='orthanc-events', subjects=['onchange'])
    finally:
        await nc.close()


def get_nats_url():
    return os.getenv('NATS_URL', 'nats://localhost:54222')


async def publish_to_nats(evt, *_):
    nc = await nats.connect(get_nats_url())
    try:
        js = nc.jetstream()
        _, message = convert_change_event_to_message(evt)
        return await js.publish('onchange', message, stream='orthanc-events')
    finally:
        await nc.close()
