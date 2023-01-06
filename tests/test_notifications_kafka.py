from kafka3 import KafkaProducer

import pytest
from dockercontext import container as containerlib


@pytest.fixture(scope='session')
def docker_kafka():
    with containerlib.Context(
            'docker.redpanda.com/vectorized/redpanda:latest', {'9092/tcp': 9092}) as container:
        print(container.container.logs().decode('ascii'))
        yield container


def test_publish(docker_kafka):
    producer = KafkaProducer(security_protocol='PLAINTEXT', bootstrap_servers='localhost:9092')
    producer.send('foobar', b'some_message_bytes')
