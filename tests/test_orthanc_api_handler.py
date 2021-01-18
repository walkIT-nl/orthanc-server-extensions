import responses
from orthanc_ext.orthanc import OrthancApiHandler

orthanc = OrthancApiHandler()


@responses.activate
def test_delete_should_forward_to_requests():
    responses.add(responses.DELETE, 'https://localhost:8042/test',
                  json={}, status=202)

    orthanc.RestApiDelete('/test')
