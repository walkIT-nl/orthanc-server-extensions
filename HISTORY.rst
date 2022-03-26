=======
History
=======

3.2.8 (2021-09-18)
------------------
* get_metadata_of_first_instance_of_series() now propagates http errors if /instances call fails.

3.2.7 (2021-09-17)
------------------
* Small resilience fix for httpx (more conservative timeouts)
* get_metadata_of_first_instance_of_series() will now return None for unknown keys

3.2.6 (2021-09-16)
------------------

* Replace requests/responses library by httpx/respx
* Add support for anonymization and re-identification using study merge
* Many smaller and bigger refactorings
* Dependency updates

3.1.1 (2021-02-11)
------------------

* Add DICOM auto forwarding sample with retries

3.1.0 (2021-02-07)
------------------

* Improved logging, aligned log format and levels with Orthanc.

0.1.0 (2021-01-09)
------------------

* First release on PyPI.
