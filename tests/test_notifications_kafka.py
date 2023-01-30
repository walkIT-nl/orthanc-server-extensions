from functools import partial

import httpx
import pytest
from aiokafka import AIOKafkaConsumer
from dockercontext import container as containerlib

from orthanc_ext import event_dispatcher
from orthanc_ext.http_utilities import create_internal_client, ClientType
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.scripts.event_publisher import convert_message_to_change_event
from orthanc_ext.scripts.kafka_event_publisher import create_stream, publish_to_kafka, KafkaConfig

exposed_port = 9092


@pytest.fixture
def kafka_config():
    bootstrap_server = f'localhost:{exposed_port}'
    return KafkaConfig(bootstrap_server)


@pytest.fixture
def async_client():
    return create_internal_client('https://localhost:8042', '', client_type=ClientType.ASYNC)


@pytest.fixture(scope='session')
def orthanc():
    yield OrthancApiHandler()


@pytest.fixture(scope='session')
def docker_kafka():
    with containerlib.Context(
            'docker.redpanda.com/vectorized/redpanda:latest', {'9092/tcp': exposed_port},
            'redpanda start --check=false') as container:
        print(container.container.logs().decode('ascii'))
        yield container


def test_registered_callback_should_be_notify_change_event(
        docker_kafka, orthanc, async_client, kafka_config):
    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.ORTHANC_STARTED: [partial(create_stream, kafka_config)],
        orthanc.ChangeType.STABLE_STUDY:
            [partial(publish_to_kafka, kafka_config),
             partial(get_first_message, kafka_config)],
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


async def get_first_message(kafka_config, evt, *_):
    consumer = AIOKafkaConsumer(
        'orthanc-events',
        security_protocol='PLAINTEXT',
        bootstrap_servers=kafka_config.bootstrap_server,
        consumer_timeout_ms=1000,
        auto_offset_reset='earliest')
    await consumer.start()
    try:
        async for msg in consumer:
            print(
                'consumed: ', msg.topic, msg.partition, msg.offset, msg.key, msg.value,
                msg.timestamp)
            break
    finally:
        await consumer.stop()

    return msg.value
