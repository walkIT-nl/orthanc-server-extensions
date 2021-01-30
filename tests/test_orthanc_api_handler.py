from orthanc_ext.orthanc import OrthancApiHandler

orthanc = OrthancApiHandler()


def test_GenerateRestApiAuthorizationToken_should_yield_a_token():
    assert orthanc.GenerateRestApiAuthorizationToken() is not None
