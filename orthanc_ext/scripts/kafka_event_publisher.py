from dataclasses import dataclass

from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from orthanc_ext.scripts.event_publisher import convert_change_event_to_message


@dataclass
class KafkaConfig:
    bootstrap_server: str
    topic: str = 'orthanc-events'


async def publish_to_kafka(kafka_config: KafkaConfig, evt, _):
    producer = AIOKafkaProducer(
        security_protocol='PLAINTEXT', bootstrap_servers=kafka_config.bootstrap_server)
    await producer.start()
    try:
        _, event = convert_change_event_to_message(evt)
        await producer.send_and_wait(kafka_config.topic, event)

    finally:
        await producer.stop()


async def create_stream(kafka_config: KafkaConfig, *_):
    async with AIOKafkaAdminClient(bootstrap_servers=kafka_config.bootstrap_server,
                                   request_timeout_ms=10000) as admin_client:
        await admin_client.start()

        await admin_client.create_topics(
            new_topics=[NewTopic(name=kafka_config.topic, num_partitions=1, replication_factor=1)],
            validate_only=False)
