import httpx
import pytest
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from dockercontext import container as containerlib
from kafka.admin import KafkaAdminClient, NewTopic

from orthanc_ext import event_dispatcher
from orthanc_ext.orthanc import OrthancApiHandler

exposed_port = 9092
bootstrap_server = f'localhost:{exposed_port}'


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


def test_registered_callback_should_be_notify_change_event(docker_kafka, orthanc):
    event_dispatcher.register_event_handlers({
        orthanc.ChangeType.ORTHANC_STARTED: [create_stream],
        orthanc.ChangeType.STABLE_STUDY: [notify_kafka, get_first_message],
    }, orthanc, httpx)

    orthanc.on_change(
        orthanc.ChangeType.ORTHANC_STARTED, orthanc.ResourceType.NONE, 'resource-uuid')

    return_values = orthanc.on_change(
        orthanc.ChangeType.STABLE_STUDY, orthanc.ResourceType.STUDY, 'resource-uuid')

    assert return_values == [None, b'some_message_bytes']


async def notify_kafka(*_):
    producer = AIOKafkaProducer(security_protocol='PLAINTEXT', bootstrap_servers=bootstrap_server)
    await producer.start()
    try:
        await producer.send_and_wait('orthanc-events', b'some_message_bytes')
    finally:
        await producer.stop()


async def get_first_message(evt, *_):
    consumer = AIOKafkaConsumer(
        'orthanc-events',
        security_protocol='PLAINTEXT',
        bootstrap_servers=bootstrap_server,
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


def create_stream(*_):
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_server)
    admin_client.create_topics(
        new_topics=[NewTopic(name='orthanc-events', num_partitions=1, replication_factor=1)],
        validate_only=False)
