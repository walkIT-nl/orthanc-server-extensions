FROM osimis/orthanc

COPY orthanc_ext /python/orthanc_ext
COPY tests/entry_point.py /python/entry_point.py
