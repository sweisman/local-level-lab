# The saved ESA forecasts stay apart after allowing smooth errors

All three pairs of forecasts on the opened ESA flight remained well
separated in the working covariance metric after allowing a separate
cubic position error for each candidate. Across 24 comparisons, at least
**86% of the squared separation remained**. The calculation used saved
paths and earlier receiver weights only.

| Pair | Full distance in standardized units | Distance allowing cubic error | Variance multiple at the illustrative 80% power limit |
|---|---:|---:|---:|
| Specified-field globe and disc | 28.4–31.7 | 28.3–29.5 | 80.0–86.5 |
| Specified-field globe and zero-field globe | 22.1–25.2 | 22.0–23.8 | 48.4–56.2 |
| Zero-field globe and disc | 25.2–26.3 | 25.2–26.1 | 63.2–67.7 |

The ranges cover both complete fitted-removal settings, both drift laws
and both receiver weightings. The two zero-removal settings remain
incomplete. The label *zero-field globe* refers to the physical
candidate whose specified background field is zero. The complete
settings still allow a fitted processing term for each candidate.

For two exact forecast means with a known common Gaussian covariance,
the best direction for distinguishing them is their difference after
whitening. Its power at test size (alpha) is
(Phi(d-Phi^{-1}(1-alpha))), where (d) is the distance in the
table. The last column uses an illustrative 1% size and allows the
entire covariance to grow by a common factor. Projecting out the
smooth terms allows those errors to be unrestricted. The calculation
keeps the remaining model paths and covariance structure fixed.

The benchmark shows that, for these fixed paths, a cubic mean error or
moderate common variance increase would leave substantial separation.
It does not measure aircraft power. Calibration can change the
forecasts outside that smooth subspace, and the aircraft covariance
and physical adequacy still need to qualify. No later receiver
observation, reserved flight or new fit was used.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.forecast_pair_information replay
```

[Fixed design](FORECAST_PAIR_INFORMATION_PLAN.md) ·
[Frozen inputs](forecast-pair-information-freeze.json) ·
[All pair distances](forecast-pair-information-result.json)
