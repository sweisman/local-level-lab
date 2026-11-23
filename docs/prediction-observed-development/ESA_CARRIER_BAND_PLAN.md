# Compare the two GPS bands on the existing aircraft–ground score

Use the fixed 120 one-second intervals and satellite weights from the
archived Qaqortoq score for development flight 187. Hold the time window,
satellites and weights fixed. Read only the saved aircraft and ground
receiver excerpts. Retain unavailable intervals if an original satellite
arc cannot reproduce, and make no assertion for the omitted directions.

For each satellite, compute the difference between the L1 and L2 carrier
changes in metres. Require the same L2 tracking code at both sites and
continuous locking, including the aircraft's intermediate half-second
report. Divide by the squared frequency ratio minus one. The result is
the exact additive change from the measured L1 carrier increment to the
two-frequency, first-order ionosphere-free increment. Take its signed
projection through the original weights for each station and their
difference. Report RMS and correlation on the same satellite rows.
[ESA carrier combinations](https://gssc.esa.int/navipedia/index.php/Combination_of_GNSS_Measurements)

Common range and clock terms cancel between the bands. The remainder
contains changing ionospheric delay and can also contain receiver noise,
antenna effects and other frequency-dependent errors. It measures the
contribution of the band correction, without treating that correction as
an uncertainty bound on the remaining two-frequency aircraft solution.

Allow at most two saved receiver excerpts, 120 intervals and 32 satellites
per interval on one thread. Use no orbits, Earth-model propagation, new
fits or reserved-flight measurements. Freeze the code, exact source hashes
and environment before evaluation.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_carrier_band_replay freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_carrier_band_replay check
```
