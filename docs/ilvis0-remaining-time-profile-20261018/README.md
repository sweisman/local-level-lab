# Testing the remaining time-alignment disagreement

One unresolved stretch has different best-saved IMU-to-GPS time offsets on repeat.
This study asks whether both starting solutions reach the same calibration fit
when time is held fixed. It covers both processing assumptions and preserves
the original physical models, measurements and error bounds.

The [finite plan](PLAN.md) permits eight restricted fits and two controls:
**654 native calls maximum, four threads, no retries**. Software qualification
and source/input checks must pass before any archival start. Conditional fits
remain diagnostic and cannot change the [published findings](../CURRENT_STATUS.md).

The launcher writes status and per-call receipts under
`data/ilvis0-remaining-time-profile-20261018/` and publishes `RESULTS.md` automatically
after completion. Routine status is available through `analysis/status.py`.

[Next analyses](../NEXT_STEPS.md) · [Study index](../STUDIES.md).
