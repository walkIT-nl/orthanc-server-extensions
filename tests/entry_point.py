"""Test entry point script for Orthanc Python Plugin.
"""
import asyncio
import atexit
import logging
import time
from functools import partial

import orthanc  # NOQA provided by the plugin runtime.

from orthanc_ext import event_dispatcher
from orthanc_ext.executor_utilities import AsyncOnlyExecutor
from orthanc_ext.http_utilities import ClientType
from orthanc_ext.python_utilities import pipeline
from orthanc_ext.scripts.nats_event_publisher import create_stream, publish_to_nats, NatsConfig


async def log_event(param, event, _):
    logging.info(f'orthanc "{event}" event handled with param "{param}"')


def start_maintenance_cycle(event, _):
    logging.info(f'do something special on "{event}"')


def retrieve_system_info(_, client):
    return client.get('/system').json()


def show_system_info(info, _client):
    version = info.get('Version')
    logging.warning(f'orthanc version retrieved: "{version}"', )


async def series(client):
    return await client.get('/series/f456be9b-051601b8-aa7f00b0-68ff9ff5-4aae6cce')


async def studies(client):
    return await client.get('/studies/4dd19b2b-1728426d-623a4fab-ba151c31-33482e59')


async def gather(_res, client):
    infos = await asyncio.gather(series(client), studies(client), return_exceptions=True)
    print(infos)
    return infos


def block_python(*_):
    time.sleep(10)


nats_config = NatsConfig('nats://nats')
executor = event_dispatcher.register_event_handlers({
    orthanc.ChangeType.ORTHANC_STARTED: [
        partial(log_event, 'started'),
        partial(create_stream, nats_config), start_maintenance_cycle,
        pipeline(retrieve_system_info, show_system_info), gather,
    ],
    orthanc.ChangeType.NEW_INSTANCE:
        [partial(log_event, 'new instance'),
         partial(publish_to_nats, nats_config)],
    orthanc.ChangeType.ORTHANC_STOPPED: [partial(log_event, 'stopped'), AsyncOnlyExecutor.stop]
},
                                                    orthanc,
                                                    event_dispatcher.create_session(orthanc),
                                                    event_dispatcher.create_session(
                                                        orthanc, client_type=ClientType.ASYNC),
                                                    handler_executor=AsyncOnlyExecutor)

executor.start()
atexit.register(executor.stop)
