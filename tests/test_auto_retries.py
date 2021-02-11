import logging

import responses

from orthanc_ext import event_dispatcher
from orthanc_ext.orthanc import OrthancApiHandler
from orthanc_ext.scripts.auto_retries import handle_failed_forwarding_job, calculate_delay, ONE_MINUTE, ONE_DAY

orthanc = OrthancApiHandler()
session = event_dispatcher.create_internal_requests_session('https://localhost:8042', '')


def test_calculate_delay():
    job = {
        "CompletionTime": "20210210T084933.795611",
        "Content": {
            "Description": "REST API",
            "FailedInstancesCount": 0,
            "InstancesCount": 1,
            "LocalAet": "ORTHANC",
            "ParentResources": [
                "3121d449-9b15610c-df9b8396-bee611db-3901f794"
            ],
            "RemoteAet": "PYNETDICOM"
        },
        "CreationTime": "20210210T084350.430751",
        "EffectiveRuntime": 0.036999999999999998,
        "ErrorCode": 9,
        "ErrorDescription": "Error in the network protocol",
        "ID": "0a9b0d5f-a2a8-46c1-8b2a-6a1e081427fb",
        "Priority": 0,
        "Progress": 0,
        "State": "Failure",
        "Timestamp": "20210210T090925.594915",
        "Type": "DicomModalityStore"
    }

    assert calculate_delay(job) == 686


def test_calculate_delay_shall_not_retry_too_aggressively():
    # interval first try: 1 second
    job = {"CreationTime": "20210210T084350.430751", "CompletionTime": "20210210T084351.430751"}

    assert calculate_delay(job) == ONE_MINUTE


def test_calculate_delay_shall_use_back_off():
    # time between previous tries: 3 minutes
    job = {"CreationTime": "20210210T084350.430751", "CompletionTime": "20210210T084650.430751"}

    assert calculate_delay(job) == 6 * ONE_MINUTE

    job = {"CreationTime": "20210210T084350.430751", "CompletionTime": "20210210T085250.430751"}

    assert calculate_delay(job) == 18 * ONE_MINUTE


def test_calculate_delay_shall_retry_every_day():
    job = {"CreationTime": "20210210T084350.430751", "CompletionTime": "20210210T224350.430751"}

    assert calculate_delay(job) == ONE_DAY


@responses.activate
def test_should_not_resubmit_other_job_types(caplog):
    caplog.set_level(logging.DEBUG)

    job = {"CreationTime": "20210210T084350.430751", "CompletionTime": "20210210T224350.430751",
           "Type": "CreateDicomZip"}

    responses.add(responses.GET, 'https://localhost:8042/jobs/job-uuid',
                  json=job)

    event_dispatcher.register_event_handlers(
        {
            orthanc.ChangeType.JOB_FAILURE: handle_failed_forwarding_job(0.1),
        }, orthanc_module=orthanc, requests_session=session)
    orthanc.on_change(orthanc.ChangeType.JOB_FAILURE, '', 'job-uuid')

    assert caplog.messages == ["not retrying 'CreateDicomZip' job 'job-uuid'"]


@responses.activate
def test_on_failure_should_resubmit_job(caplog):
    caplog.set_level(logging.DEBUG)

    responses.add(responses.GET, 'https://localhost:8042/jobs/job-uuid',
                  json={"CreationTime": "20210210T084350.430751", "CompletionTime": "20210210T084351.430751",
                        "Type": "DicomModalityStore"})

    # TODO: figure out why expectation not met in Timer thread.
    responses.add(responses.POST, 'https://localhost:8042/jobs/job-uuid/resubmit', {})

    event_dispatcher.register_event_handlers(
        {
            orthanc.ChangeType.JOB_FAILURE: handle_failed_forwarding_job(0.1),
        }, orthanc_module=orthanc, requests_session=session)
    orthanc.on_change(orthanc.ChangeType.JOB_FAILURE, '', 'job-uuid')

    assert caplog.messages == ["resubmitting job 'job-uuid' after 2 seconds"]
