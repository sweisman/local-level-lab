# The changing-drift range covers the ESA forecasts but loses separation

The later receiver positions fell inside the ranges from all 20 scorable
forecasts on ESA development recording 187 under both receiver weighting cases. In the two
complete three-model settings, all model ranges overlapped at every later
epoch. Four original flat-disc starts remain unresolved.

The error law used only the earlier 400 reports to correct each forecast.
In one complete setting, with fixed 3 cm receiver scatter, the errors over
the later 120 reports were:

| Candidate | Raw positional RMS | Size of the correction, RMS | Corrected positional RMS |
|---|---:|---:|---:|
| Globe with specified field | 5.23 m | 5.60 m | 1.24 m |
| Globe with zero field | 2,595 m | 2,590 m | 12.69 m |
| Stationary flat disc | 4,006 m | 3,996 m | 18.78 m |

The other complete setting gave nearly identical results. Across all starts,
both receiver weighting cases gave descriptive accuracy passes for all 20
corrected paths over the first 60 reports. Over 120 reports, only the eight
specified-field globe paths passed that screen. The fixed-3-cm half-width
grew from about 30 m per axis at 60 reports to 199 m at 120. That wide range
covered the later reports even for paths that failed the accuracy screen.

The correction can absorb kilometre-scale model differences. Range
containment alone is therefore too permissive to test the candidates here.
This is one selected development flight. The replay kept the generated
process scales, used a longer horizon and omitted fitted calibration
uncertainty. It earns no aircraft coverage claim. The seven reserved ESA
groups remain closed.

The earlier-only ranges were sealed before scoring. Independent replay
reproduced the range archive and score receipt byte for byte. To reproduce
from the repository root, run the following command, then repeat it with
`score` as the final argument.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_changing_drift_transfer condition
```

[Method](ESA_CHANGING_DRIFT_TRANSFER_PLAN.md) · [Frozen inputs](esa-changing-drift-transfer-freeze.json) ·
[Earlier-only range seal](esa-changing-drift-transfer-range-seal.json) · [All scores](esa-changing-drift-transfer-result.json)

The [earlier-only correction audit](ESA_DRIFT_CORRECTION_AUDIT_RESULT.md)
traces nearly all of the kilometre-scale correction to the changing inertial
drift terms. Receiver terms contribute less than 0.14 m RMS.
