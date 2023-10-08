import httpx

from orthanc_ext.event_dispatcher import create_session
from orthanc_ext.http_utilities import ClientType
from orthanc_ext.orthanc import OrthancApiHandler


def test_shall_create_sync_client():
    client = ClientType.create_internal_client(base_url='http://localhost:8042')
    assert client is not None
    assert type(client) == httpx.Client


def test_shall_support_create_session_for_backward_compatibility():
    assert create_session(OrthancApiHandler(), ClientType.SYNC) is not None
