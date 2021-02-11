import logging
import threading
from datetime import datetime

ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
ONE_DAY = 24 * ONE_HOUR


def handle_failed_forwarding_job(first_retry=ONE_MINUTE, job_types=['DicomModalityStore']):
    def handle_failed_forwarding_job(event, session):
        job_id = event.resource_id
        resp = session.get(f'/jobs/{job_id}')
        resp.raise_for_status()

        job = resp.json()
        job_type = job['Type']
        if job_type not in job_types:
            logging.debug(f"not retrying '{job_type}' job '{job_id}'")
            return

        delay = calculate_delay(job, first_retry)
        logging.debug(f"resubmitting job '{job_id}' after {delay} seconds")
        timer = threading.Timer(interval=delay,
                                function=resubmit_job,
                                args=[session, job_id, delay])
        timer.start()

    return handle_failed_forwarding_job


def calculate_delay(job, first_retry=ONE_MINUTE):
    elapsed = parse_time(job['CompletionTime']) - parse_time(job['CreationTime'])
    return min(max(first_retry, elapsed.seconds * 2), ONE_DAY)


def parse_time(job_time):
    return datetime.strptime(job_time, '%Y%m%dT%H%M%S.%f')


def resubmit_job(session, job_id, delay):
    resp = session.post(f'/jobs/{job_id}/resubmit')
    resp.raise_for_status()
    logging.info(f'resubmitted job {job_id}')
