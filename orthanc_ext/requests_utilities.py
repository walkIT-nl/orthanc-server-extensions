from requests_toolbelt import sessions


def get_rest_api_base_url(config):
    port = config.get('HttpPort', 8042)
    scheme = 'https' if config.get('SslEnabled', False) else 'http'
    return f'{scheme}://localhost:{port}/'


def get_certificate(config):
    return config.get('SslCertificate', False)


def create_internal_requests_session(base_url, token, cert=False):
    session = sessions.BaseUrlSession(base_url)
    session.headers['Authorization'] = token
    session.verify = cert
    return session
