import dataclasses
import logging

from orthanc_ext.orthanc_utilities import get_parent_study_url


@dataclasses.dataclass
class AnonymizationRequest:
    Force: bool = False
    KeepPrivateTags: bool = False
    Permissive: bool = False
    Keep: list = dataclasses.field(
        default_factory=lambda: ['StudyDescription', 'SeriesDescription'])


@dataclasses.dataclass
class ModificationResponse:
    ID: str
    Path: str
    PatientID: str
    Type: str


@dataclasses.dataclass
class ModificationRequest:
    Force: bool = False
    KeepPrivateTags: bool = False
    Permissive: bool = True

    Keep: list = dataclasses.field(
        default_factory=lambda: ['StudyDescription', 'SeriesDescription'])


def anonymize_series(client, series_id):
    resp = client.post(
        f'/series/{series_id}/anonymize', json=dataclasses.asdict(AnonymizationRequest()))
    resp.raise_for_status()

    response = ModificationResponse(**resp.json())
    logging.info(f'Anonymized "/series/{series_id}" to "{response.Path}"')

    return response


def reidentify_series(client, anonymized_series_id, original_series_id):
    parent_study_url = get_parent_study_url(client, original_series_id)
    resp = client.post(f'{parent_study_url}/merge', json={'Resources': [anonymized_series_id]})
    resp.raise_for_status()
    return resp.json()
