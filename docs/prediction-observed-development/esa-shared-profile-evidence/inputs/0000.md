# Recover the shared calibration terms across the ESA history

Use the archived zero-field globe and disc fits, 155,868 original
packets and 520 saved forecast queries from ESA recording 187. Restore
the same scalar integrator and verify its antenna positions against all
saved forecasts within one micrometre. Set the lever coordinates to
zero in a second output-only call to obtain the body positions that
define the geographic metric. The original fitted calibration stays sealed.

Construct the 24 shared coefficient columns at every query. The first
six include the clock–velocity and lever terms. The next nine use the
same reference acceleration across the record. The final nine use the
exact force integrals on the original packet clock. Compare all 24
columns at the first two queries with the
[sealed interval reports](ESA_SOURCE_TRANSFER_CHECK.md).

Use two one-thread workers. Each task permits two scalar value calls,
one exact force scan, and at most 180 cooperative wall seconds for the
study. There are no new fits, later receiver reads or reserved groups.
This recovers a coefficient profile for a saved-data bound. It does
not propagate the unshared nonlinear remainder over the aircraft history.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_shared_profile
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-shared-profile-v1-20261119 --reserved-threads 0
```
