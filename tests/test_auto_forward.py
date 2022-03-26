import logging

import respx

from orthanc_ext.event_dispatcher import register_event_handlers
from orthanc_ext.http_utilities import create_internal_client
from orthanc_ext.logging_configurator import python_logging
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.orthanc_utilities import (get_metadata_of_first_instance_of_series)
from orthanc_ext.scripts.auto_forward import (forward_dicom, DicomReceivedMatcher)

orthanc = OrthancApiHandler()
client = create_internal_client('https://localhost:8042')


def register_and_trigger_handler(matchers):
    register_event_handlers({orthanc.ChangeType.STABLE_STUDY: forward_dicom(matchers)},
                            orthanc,
                            client,
                            logging_configuration=python_logging)
    orthanc.on_change(orthanc.ChangeType.STABLE_STUDY, '', 'study-uuid')


def is_not_dicom_origin(resource_id, client):
    return get_metadata_of_first_instance_of_series(
        client, resource_id, 'Origin') != 'DicomProtocol'


@respx.mock
def test_autoforward_on_match_shall_start_start_modality_store(caplog):
    store = respx.post('/modalities/pacs/store').respond(200, text='study-uuid')
    register_and_trigger_handler([DicomReceivedMatcher(lambda uid, _: True, lambda uid, _: 'pacs')])
    assert store.called
    assert caplog.messages == ['DICOM export to modality "pacs" started for resource "study-uuid"']


@respx.mock
def test_autoforward_on_multiple_matches_shall_start_start_modality_store(caplog):
    instances = respx.get('/series/study-uuid/instances').respond(
        200, json=[{
            'ID': 'b99cd218-ae67f0d7-70324b6b-2b095801-f858dedf'
        }])
    origin = respx.get(
        '/instances/b99cd218-ae67f0d7-70324b6b-2b095801-f858dedf'
        '/metadata/Origin').respond(
            200, text='Plugins')
    pacs1 = respx.post('/modalities/pacs1/store').respond(200, text='study-uuid')
    pacs2 = respx.post('/modalities/pacs2/store').respond(200, text='study-uuid')
    caplog.set_level(logging.INFO)
    matcher1 = DicomReceivedMatcher(is_not_dicom_origin, lambda uid, _: 'pacs1')
    matcher2 = DicomReceivedMatcher(lambda uid, _: True, lambda uid, _: 'pacs2')
    register_and_trigger_handler([matcher1, matcher2])
    assert instances.called
    assert origin.called
    assert pacs1.called
    assert pacs2.called
    assert caplog.messages == [
        'DICOM export to modality "pacs1" started for resource "study-uuid"',
        'DICOM export to modality "pacs2" started for resource "study-uuid"'
    ]


def test_autoforward_on_no_match_shall_log_and_continue(caplog):
    register_and_trigger_handler([
        DicomReceivedMatcher(lambda uid, _: False, lambda uid, _: 'pacs')
    ])
    (message, ) = caplog.messages
    assert 'did not match; resource "study-uuid" not forwarded' in message
