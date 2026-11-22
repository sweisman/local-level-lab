# GNSS velocity consistency on the earlier-only fit input

**Question:** Does the GNSS-only PPP export's reported velocity agree with the time derivative of its reported positions over the already sealed first 400 receiver reports?

Use only the sealed 400-report `training` input of the completed ESA earlier-origin fit. Compute the centered latitude, longitude and height derivative at interior epochs using the actual time tags and WGS84 meridional/prime-vertical radii. Compare north/east/up components with the export's reported velocities. Report signed mean and RMS discrepancy by axis, count, source hashes and the exclusion of the two derivative endpoints. Do not inspect later receiver reports or refit an Earth model.

This is an exploratory internal-consistency check; its design followed inspection of the 400-report development data. Agreement does not make velocity independent of position or establish the export covariance's calibration. It cannot qualify the motion error law alone. A separate source-format check and known-answer test must precede publication.

Implementation: add a shared WGS84 derivative helper and saved-input report in `analysis/lll/esa_gnss_velocity_consistency.py`; test it on an independently calculated constant-speed path in `analysis/tests/test_esa_gnss_velocity_consistency.py`. Write the report beside the other 400/120 development controls.
