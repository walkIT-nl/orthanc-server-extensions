import httpx


def get_rest_api_base_url(config):
    port = config.get('HttpPort', 8042)
    scheme = 'https' if config.get('SslEnabled', False) else 'http'
    return f'{scheme}://localhost:{port}/'


def get_certificate(config):
    return config.get('SslCertificate', False)


def create_internal_client(base_url, token='', cert=None) -> httpx.Client:
    return httpx.Client(
        base_url=base_url,
        verify=cert if cert is not None else False,
        headers={'Authorization': token})
