import datetime
import logging
import threading

ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = 24 * ONE_HOUR

RETRYABLE_JOBTYPES = {'DicomModalityStore'}


def parse_time(job_time):
    return datetime.datetime.strptime(job_time, '%Y%m%dT%H%M%S.%f')


def calculate_delay(job, first_retry=ONE_MINUTE):
    elapsed = parse_time(job['CompletionTime']) - parse_time(job['CreationTime'])
    return min(max(first_retry, elapsed.seconds * 2), ONE_DAY)


def resubmit_job(client, job_id):
    resp = client.post(f'/jobs/{job_id}/resubmit')
    resp.raise_for_status()
    logging.info(f'resubmitted job "{job_id}"')


def python_timer_runner(job_id, delay, client):
    timer = threading.Timer(interval=delay, function=resubmit_job, args=[client, job_id])
    timer.start()


def handle_failed_forwarding_job(
        first_retry=ONE_MINUTE, job_types=RETRYABLE_JOBTYPES, job_runner=python_timer_runner):

    def handle_failed_forwarding_job(event, client):
        job_id = event.resource_id
        response = client.get(f'/jobs/{job_id}')
        response.raise_for_status()
        job = response.json()
        job_type = job['Type']
        if job_type not in job_types:
            logging.debug(f'not retrying "{job_type}" job "{job_id}"')
            return
        delay = calculate_delay(job, first_retry)
        logging.debug(f'resubmitting job "{job_id}" after {delay} seconds')
        return job_runner(job_id, delay, client)

    return handle_failed_forwarding_job
