# The narrower drift law misses more known-answer histories

Removing the changing-jerk term reduced the median 60-report half-width
from **29.57 m to 14.82 m**. With the same 4.2 threshold, the narrower law
missed **59 of 256** generated later paths. The original law missed one.
Both laws were scored on the same saved errors.

| Generated condition | Histories | Original misses | Narrower-law misses | New misses |
|---|---:|---:|---:|---:|
| Without vibration | 128 | 1 | 28 | 27 |
| With vibration | 128 | 0 | 31 | 31 |

The original gate allowed one miss per stratum. The narrower law fails
that check by a wide margin. This is the same change that improved shape
separation on [one ESA development flight](ESA_NO_SNAP_ABLATION_RESULT.md).
Taken together, the two checks expose a trade-off between covering the
generated drift and preserving the aircraft model contrast.

The numerical replay reproduced all 256 original scores and formed every
new range from the earlier errors. It used no new simulations, fits,
aircraft files or reserved flight groups. It reuses the original cohort
as a diagnostic and carries no new coverage claim.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_no_snap_generated_backcheck replay
```

[Fixed method](ESA_NO_SNAP_GENERATED_BACKCHECK_PLAN.md) ·
[Frozen inputs](esa-no-snap-generated-backcheck-freeze.json) ·
[All paired scores](esa-no-snap-generated-backcheck-result.json)
