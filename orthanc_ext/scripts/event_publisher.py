import dataclasses

from cloudevents.conversion import to_structured, from_http
from cloudevents.http import CloudEvent


def create_valid_orthanc_cloud_event(evt):
    return CloudEvent.create({
        'type': 'orthanc-server-extensions.change-event',
        'source': 'https://orthanc-server-identifer'
    },
                             data=dataclasses.asdict(evt))


def convert_change_event_to_message(evt) -> tuple:
    return to_structured(create_valid_orthanc_cloud_event(evt))


def convert_message_to_change_event(headers: dict, data: bytes):
    return from_http(CloudEvent, headers, data=data)
