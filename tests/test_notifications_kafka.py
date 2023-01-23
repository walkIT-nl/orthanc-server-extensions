from kafka3 import KafkaProducer, KafkaConsumer
from kafka3.admin import KafkaAdminClient, NewTopic

import pytest
from dockercontext import container as containerlib

exposed_port = 59092
bootstrap_server = f'localhost:{exposed_port}'


@pytest.fixture(scope='session')
def docker_kafka():
    with containerlib.Context(
            'docker.redpanda.com/vectorized/redpanda:latest', {'9092/tcp': exposed_port},
            'redpanda start --check=false') as container:
        print(container.container.logs().decode('ascii'))
        yield container


def test_publish(docker_kafka, topic='foobar'):
    admin_client = KafkaAdminClient(bootstrap_servers=bootstrap_server)
    admin_client.create_topics(
        new_topics=[NewTopic(name=topic, num_partitions=1, replication_factor=1)],
        validate_only=False)
    producer = KafkaProducer(security_protocol='PLAINTEXT', bootstrap_servers=bootstrap_server)
    consumer = KafkaConsumer(
        topic,
        security_protocol='PLAINTEXT',
        bootstrap_servers=bootstrap_server,
        consumer_timeout_ms=1000,
        auto_offset_reset='earliest')

    producer.send(topic, b'some_message_bytes')

    assert b'some_message_bytes' == next(consumer).value
