import logging

import respx

from orthanc_ext.http_utilities import create_internal_client
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.scripts.anonymization import anonymize_series, reidentify_series

orthanc = OrthancApiHandler()
client = create_internal_client('https://localhost:8042')


@respx.mock
def test_anonymization_shall_leverage_orthanc_builtin_functionality(caplog):
    caplog.set_level(logging.INFO)
    store = respx.post('/series/1.2.3/anonymize').respond(
        200, json={
            'ID': 1,
            'Path': '/series/1.2.4',
            'PatientID': '123',
            'Type': 'boe'
        })
    anonymize_series(client, '1.2.3')
    assert store.called
    assert caplog.messages == ['Anonymized "/series/1.2.3" to "/series/1.2.4"']


@respx.mock
def test_reidentify_series_shall_leverage_orthanc_merge_to_replace_patient_study_module_tags(
        caplog):
    caplog.set_level(logging.INFO)

    get_series = respx.get('/series/7052c73b-da85938f-1f05fa57-2aae3a3f-76f4e628').respond(
        200, json={'ParentStudy': '0293e107-c1439ada-0bd307cd-f98de2c2-9245e619'})
    merge_series = respx.post(
        '/studies/0293e107-c1439ada-0bd307cd-f98de2c2-9245e619/merge').respond(
            200,
            json={
                'Description': 'REST API',
                'FailedInstancesCount': 0,
                'InstancesCount': 12,
                'TargetStudy': '0293e107-c1439ada-0bd307cd-f98de2c2-9245e619'
            })

    reidentify_series(client, 'uuid-ano', '7052c73b-da85938f-1f05fa57-2aae3a3f-76f4e628')

    assert get_series.called
    assert merge_series.called
