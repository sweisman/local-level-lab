# Raw GPS carrier phase confirms the later relative motion

The position path reconstructed from raw GPS carrier-phase changes
agreed with the original export to **7.1 cm horizontal RMS** and
**10.0 cm height RMS** over the two-minute prediction period. The
three-dimensional RMS difference was **12.3 cm**. The replay started
at the last earlier export position and used no later position resets.

Each of the **240** half-second motion steps passed with at least ten
GPS satellites. The replay used the same broadcast ephemeris at
both endpoints of each step and estimated a freely changing receiver
clock. Reevaluating the atmosphere correction at the preliminary end
position changed a step by at most 3.0 mm.

| Later positions used for scoring | Fixed shape score |
| --- | ---: |
| Original export | −6.923 |
| Carrier-phase path | −7.131 |

Zero is a tie. Both paths give the zero-field globe a smaller
forecast error than the zero-field disc under the same working
weights and smooth adjustment. The carrier-phase path moves the score
by **−0.208** units. The earlier receiver positions, the two fitted
calibrations and the archived forecasts stay fixed.

This compares relative motion measured through two processing paths
on one flight. Both paths use signals from the same antenna. Their
agreement constrains differences introduced by the receiver processing
over these two minutes. Shared satellite and atmospheric errors,
the absolute position at the anchor, and transfer to other aircraft
still need qualification. No inertial fit or forecast propagation
ran. The reserved ESA flights remained sealed.

The [continuity inventory](ESA_CARRIER_PHASE_SUPPORT_RESULT.md) found a
gap before the prediction cut. This replay uses only the complete
segment after that gap.

## Reproduce the replay

Use the sealed earlier receiver anchor and raw RINEX excerpt from
recording 187, together with the saved broadcast navigation product.
Prepare and run in a separate reproduction directory with the frozen
numerical environment. Use only the report command for the closed study.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_carrier_phase_later prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-carrier-phase-later-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_carrier_phase_later report
```

[Fixed method](ESA_CARRIER_PHASE_LATER_PLAN.md) ·
[Saved differences and score](esa-carrier-phase-later-result.json)
