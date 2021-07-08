import dataclasses
import logging

import httpx

from typing import Callable, Iterable


@dataclasses.dataclass
class DicomReceivedMatcher:
    matches: Callable[[str, httpx.Client], bool]
    modality_selector: Callable[[str, httpx.Client], str]


def forward_dicom(matchers: Iterable[DicomReceivedMatcher]):

    def forward_series(event, client):
        resource_id = event.resource_id
        for matcher in matchers:
            if not matcher.matches(resource_id, client):
                logging.info(
                    f'matcher "{matcher}" did not match; resource '
                    f'"{resource_id}" not forwarded')
                continue
            modality = matcher.modality_selector(resource_id, client)
            resp = client.post(f'/modalities/{modality}/store', json=[resource_id])
            resp.raise_for_status()
            logging.info(
                f'DICOM export to modality "{modality}" started for '
                f'resource "{resource_id}"')

    return forward_series
