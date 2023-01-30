"""Test entry point script for Orthanc Python Plugin.
"""

import logging
from functools import partial

import orthanc  # NOQA provided by the plugin runtime.

from orthanc_ext import event_dispatcher
from orthanc_ext.http_utilities import ClientType
from orthanc_ext.python_utilities import pipeline
from orthanc_ext.scripts.nats_event_publisher import create_stream, publish_to_nats, NatsConfig


def log_event(param, event, _):
    logging.info(f'orthanc "{event}" event handled with param "{param}"')


def start_maintenance_cycle(event, _):
    logging.info(f'do something special on "{event}"')


def retrieve_system_info(_, client):
    return client.get('/system').json()


def show_system_info(info, _client):
    version = info.get('Version')
    logging.warning(f'orthanc version retrieved: "{version}"', )


nats_config = NatsConfig('nats://nats')
event_dispatcher.register_event_handlers({
    orthanc.ChangeType.ORTHANC_STARTED: [
        partial(log_event, 'started'),
        partial(create_stream, nats_config), start_maintenance_cycle,
        pipeline(retrieve_system_info, show_system_info)
    ],
    orthanc.ChangeType.STABLE_STUDY: [partial(publish_to_nats, nats_config)],
    orthanc.ChangeType.ORTHANC_STOPPED: partial(log_event, 'stopped')
}, orthanc, event_dispatcher.create_session(orthanc),
                                         event_dispatcher.create_session(
                                             orthanc, client_type=ClientType.ASYNC))
