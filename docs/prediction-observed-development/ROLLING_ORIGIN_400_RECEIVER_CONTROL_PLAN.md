# Receiver-only control for the earlier-origin window

**Question:** On the already opened ESA development recording, how well do two fixed predictions from earlier receiver positions alone forecast the same 120 reports as the sealed 400/120 IMU study?

Use the exact 400 training reports and 120 later times from the sealed fit study. Apply the existing last-minute constant-velocity and constant-course spherical rules, with their fixed 60-second training window. Neither rule reads IMU samples or later receiver values before making its forecast. Score both against the later reports using the same north/east/up error convention as the IMU score. Preserve both rules and all failures; do not choose a rule from later errors.

This is a saved-data descriptive control on one development recording. It is not another numerical fit study, an independently selected flight, a calibrated accuracy bound, or a test between Earth models. The control fixes no new scientific parameter and consumes no reserved group. Its code must bind the sealed parent and 400/120 fit identities, verify the forecast time cut, and write a hash-bearing result. Compare against both sealed IMU laws without changing those results.

Implementation: add `analysis/lll/esa_rolling_origin_400_receiver_control.py` for the sealed-input reader and public report; add one focused generated-path test and one saved-result consistency test in `analysis/tests/test_esa_rolling_origin_400_receiver_control.py`. Publish a JSON result and short Markdown interpretation beside the existing 400/120 result. Keep the long-run study receipts immutable.
