import logging
from typing import Callable, Iterable

from dataclasses import dataclass



@dataclass
class DicomReceivedMatcher:
    matches: Callable[[str], bool]
    modality_selector: Callable[[str], str]


def forward_dicom(matchers: Iterable[DicomReceivedMatcher]):
    def forward_series(event, session):
        resource_id = event.resource_id
        for matcher in matchers:
            if matcher.matches(resource_id):
                modality = matcher.modality_selector(resource_id)
                resp = session.post(f'/modalities/{modality}/store', json=[f'"{resource_id}"'])
                resp.raise_for_status()
                logging.info(f"DICOM export to modality '{modality}' started for resource '{resource_id}'")

            else:
                logging.info(f"matcher {matcher} did not match; resource '{resource_id}' not forwarded")

    return forward_series


