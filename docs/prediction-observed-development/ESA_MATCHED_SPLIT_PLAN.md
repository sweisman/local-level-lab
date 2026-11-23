# Check the training-only receiver reader on the development flight

Use the same source file and exact timestamps as the archived
[800-training, 120-withheld cut](../analysis-provenance/esa-forecast-cuts.csv)
on development recording 187. Form a separate shorter input from the last
400 training reports. Both training lengths must end at the same report and
have the same 120 later query times. The shorter input was not used in the
original fit. This check supplies input data only.

For each input, read the source once and verify its complete SHA-256, byte
count and report count. Decode only the selected earlier receiver rows.
Read only sequence, week and time from the 120 withheld reports. Require
the original stride and one-second clock continuity. Construct the two
existing receiver working weights using each input's own earlier rows.
Verify that the shorter input contains exactly the matching tail of the
longer input, for both the receiver rows and exact times. Save hashes and
counts, with no receiver coordinates in the public receipt.

The finite allowance is two passes over the named development receiver
source, four weight constructions, one thread, no raw IMU access and no
fits. A separate test replaces later coordinates and covariance values
with text that would fail the full receiver parser. Earlier inputs and
query times must still reproduce exactly when the altered test source is
bound by its own hash. The actual fit must use the exact frozen input
and the separate scoring step must verify the held-out observations.
Nothing in this check opens the seven reserved groups or qualifies an
aircraft error law.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_forecast_receiver_split_check freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_forecast_receiver_split_check check
```
