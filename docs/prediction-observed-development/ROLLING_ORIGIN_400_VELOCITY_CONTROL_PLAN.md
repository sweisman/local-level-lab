# Reported-velocity receiver control

The earlier receiver-only control used position-derived speed and missed the later 120 reports by more than 400 m. That outcome was known before this follow-up was designed. This control is therefore exploratory, not a prespecified independent validation.

Use the same sealed 400-training/120-future ESA development cut. At the last training receiver report, take its reported north/east/up velocity. Keep that vector fixed and advance the last position along a spherical constant-course path to the already sealed future times. Do not use later receiver positions, later velocity, or IMU data in the forecast. Score afterward with the same north/east/up error convention. Preserve the earlier receiver-only and IMU results unchanged. The reported velocity and its covariance come from the GNSS-only PPP export; their accuracy and correlation with its positions remain unqualified.

Implementation: add a reusable fixed-velocity forecast in `analysis/lll/receiver_only_velocity.py`; test it against a known spherical path and invalid time cuts. Add a saved-data report in `analysis/lll/esa_rolling_origin_400_velocity_control.py`, bind the sealed source and fit hashes, and publish a separate JSON/Markdown result. This follow-up makes no Earth-model decision and does not open reserved flight groups.
