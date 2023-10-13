import httpx

from orthanc_ext.event_dispatcher import create_session
from orthanc_ext.http_utilities import ClientType, HttpxClientType
from orthanc_ext.orthanc import OrthancApiHandler


def test_shall_create_sync_client():
    client = HttpxClientType.SYNC.create_internal_client(base_url='http://localhost:8042')
    assert client is not None
    assert type(client) == httpx.Client


def test_shall_support_create_session_for_backward_compatibility():
    assert type(create_session(OrthancApiHandler(), ClientType.SYNC)) == httpx.Client


def test_shall_support_create_async_client_for_backward_compatibility():
    assert type(create_session(OrthancApiHandler(), ClientType.ASYNC)) == httpx.AsyncClient
