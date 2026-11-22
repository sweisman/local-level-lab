# One carrier-phase path covers the full ESA comparison

Starting at the first earlier position, the GPS carrier-phase
reconstruction completed all **1,038 half-second steps** with at
least ten satellites. It used the separately checked receiver clock
change to cross the earlier break. There were no later position
updates or interpolated samples.

| Portion of the same continuous path | Horizontal RMS against the export | Height RMS against the export | 3D RMS against the export |
| --- | ---: | ---: | ---: |
| 400 earlier reports | 9.3 cm | 12.8 cm | 15.8 cm |
| 120 later reports | 28.3 cm | 38.1 cm | 47.5 cm |

Using the reconstructed path throughout moved the fixed shape score
from **−6.923 to −7.132**. The earlier change contributed +0.0007
through conditioning, and the later change contributed −0.2091.
This is within 0.001 score units of the separate replay that started
at the last earlier report. Both carrier replays preserve the
zero-field globe preference under the fixed working weights.

The position differences grew when the path was anchored farther
back in time. The part that aligned with the shape score changed
very little. This checks the time pattern of differences from the
export on one opened flight. Both sources share GPS signals and an
antenna. Absolute position, common atmospheric and satellite errors,
and uncertainty across flights still need evidence.

The [clock normalization](ESA_CARRIER_CLOCK_STEP_RESULT.md) passed the
original phase continuity thresholds on all 12 satellites at the
affected pair. The original raw rejection remains recorded. The
continuous run used 1,038 charged step starts, with no new inertial
fits or forecast propagations. The seven reserved flights stayed sealed.

## Reproduce the replay

Use the archived clock result, earlier receiver anchor, raw RINEX
excerpt and associated broadcast ephemerides. Prepare and run in a
separate reproduction directory with the frozen numerical environment.
For the completed study, use the report command only.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_carrier_phase_continuous prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-carrier-phase-continuous-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_carrier_phase_continuous report
```

[Fixed method](ESA_CARRIER_PHASE_CONTINUOUS_PLAN.md) ·
[Signed differences and score](esa-carrier-phase-continuous-result.json)
