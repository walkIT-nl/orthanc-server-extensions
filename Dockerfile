FROM osimis/orthanc

RUN pip3 install requests # does not get picked up in setup.py
COPY orthanc_ext /python/orthanc_ext
COPY setup.py README.rst HISTORY.rst ./
RUN python3 setup.py install
COPY tests/entry_point.py /python/entry_point.py
