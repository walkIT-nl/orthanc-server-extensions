import os

from aiokafka import AIOKafkaProducer
from kafka.admin import KafkaAdminClient, NewTopic

from orthanc_ext.scripts.event_publisher import convert_change_event_to_message


def get_kafka_bootstrap_server():
    return os.getenv('KAFKA_BOOTSTRAP_SERVER', 'localhost:9092')


async def publish_to_kafka(evt, *_):
    producer = AIOKafkaProducer(
        security_protocol='PLAINTEXT', bootstrap_servers=get_kafka_bootstrap_server())
    await producer.start()
    try:
        _, event = convert_change_event_to_message(evt)
        await producer.send_and_wait('orthanc-events', event)

    finally:
        await producer.stop()


def create_stream(*_):
    admin_client = KafkaAdminClient(bootstrap_servers=get_kafka_bootstrap_server())
    admin_client.create_topics(
        new_topics=[NewTopic(name='orthanc-events', num_partitions=1, replication_factor=1)],
        validate_only=False)
