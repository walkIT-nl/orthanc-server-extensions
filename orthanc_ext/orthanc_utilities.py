"""
Convenience methods to work with the Orthanc REST API
"""
from http.client import NOT_FOUND


def anonymize(client, series_id):
    request = {'Force': False, 'KeepPrivateTags': True, 'Permissive': True, }
    resp = client.post(f'{series_id}/anonymize', json=request)
    resp.raise_for_status()
    return resp.json()


def get_parent_study_url(client, series_id):
    resp = client.get(f'/series/{series_id}')
    resp.raise_for_status()
    series = resp.json()
    return f"/studies/{series['ParentStudy']}"


def get_metadata_of_first_instance_of_series(client, series_id, metadata_key):
    resp = client.get(f'/series/{series_id}/instances')
    resp.raise_for_status()
    instances = resp.json()
    assert len(instances) > 0, f'expected at least one instance in series {series_id}'
    resp = client.get(f'/instances/{instances[0]["ID"]}/metadata/{metadata_key}')
    if resp.status_code in [NOT_FOUND]:
        return None
    resp.raise_for_status()
    return resp.text
