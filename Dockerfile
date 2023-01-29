FROM osimis/orthanc:22.9.0-full

RUN apt-get update && ACCEPT_EULA=Y apt-get dist-upgrade -y && apt-get install -y openssl

COPY server_cert.cnf .
RUN openssl req  -nodes -new -x509 -days 3650 -keyout /etc/ssl/private/server.key -out /etc/ssl/certs/server.pem -config server_cert.cnf
RUN mkdir -p /ssl && cat /etc/ssl/private/server.key /etc/ssl/certs/server.pem  > /ssl/keyAndCert.pem

COPY orthanc_ext /python/orthanc_ext
WORKDIR /python
COPY setup.py README.rst HISTORY.rst ./
RUN pip3 install httpx .[nats-event-publisher] # does not get picked up in setup.py
RUN python3 setup.py install
COPY tests/entry_point.py /python/entry_point.py
