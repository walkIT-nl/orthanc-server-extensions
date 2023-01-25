import dataclasses
from dataclasses import dataclass

from orthanc_ext.scripts.event_publisher import convert_change_event_to_message, \
    convert_message_to_change_event


@dataclass
class ChangeEvent:
    StudyInstanceID: str
    SeriesInstanceID: str


def test_cloud_event_conversion_roundtrip():
    event = ChangeEvent('1.2.3', '4.5.6')
    headers, data = convert_change_event_to_message(event)

    assert headers == {'content-type': 'application/cloudevents+json'}
    assert type(data) == bytes
    assert dataclasses.asdict(event) == convert_message_to_change_event(headers, data).data
