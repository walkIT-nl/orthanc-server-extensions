"""
Convenience methods to work with the Orthanc REST API
"""


def get_metadata_of_first_instance_of_series(session, series_id, metadata_key):
    instances = session.get(f'/series/{series_id}/instances').json()
    assert len(instances) > 0, f"expected at least one instance in series {series_id}"
    resp = session.get(f"/instances/{instances[0]['ID']}/metadata/{metadata_key}")
    resp.raise_for_status()

    return resp.text
