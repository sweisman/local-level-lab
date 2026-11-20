# Removing the changing-jerk term restores some separation

On ESA development recording 187, removing one drift term narrowed the
120-report range from **199 m to 69 m per axis** with fixed 3 cm receiver
scatter. Only the eight specified-field globe ranges contained the complete
later receiver path. Four original flat-disc starts remain unresolved.

| Candidate | Scored starts | Later paths contained, full law | Later paths contained, reduced law | Corrected 120-report RMS, reduced law |
|---|---:|---:|---:|---:|
| Globe with specified field | 8 | 8 | 8 | 0.72–0.79 m |
| Globe with zero field | 8 | 8 | 0 | 38.1–41.4 m |
| Stationary flat disc | 4 | 4 | 0 | 63.1–64.2 m |

Both receiver weighting cases gave the same containment counts. The
specified-field globe and disc ranges were disjoint in at least one
coordinate at **28–29 of 120 epochs** in each of the two complete settings.
The two globe ranges still overlapped throughout. Only the specified-field
globe passed the descriptive accuracy screen over the full horizon.

The lower-order terms still absorbed about 3.95 km RMS of the disc's
roughly 4 km original error. Removing this term exposed how poorly that
correction predicted the later path and reduced the width of its range.
It did not establish a physical limit on drift. Standardized training
RMS remained below one for all 20 scorable starts with both receiver cases.

This is a development check on the same recording used to diagnose the
original law. The 4.2 threshold is descriptive for the altered law.
No aircraft uncertainty, coverage or scientific decision is calibrated.
The seven reserved ESA groups remain closed.

The [generated backcheck](ESA_NO_SNAP_GENERATED_BACKCHECK_RESULT.md) found 59
misses out of 256 saved histories under the narrower law. The original law
missed one. The observed separation therefore comes with a coverage cost.

The earlier-only ranges were sealed before scoring. Both stages reproduced
their saved outputs byte for byte. Run from the repository root with the
frozen Python environment, then repeat with `score` as the final argument.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_no_snap_ablation condition
```

[Fixed plan](ESA_NO_SNAP_ABLATION_PLAN.md) · [Frozen inputs](esa-no-snap-ablation-freeze.json) ·
[Range seal](esa-no-snap-ablation-range-seal.json) · [All scores](esa-no-snap-ablation-result.json)
