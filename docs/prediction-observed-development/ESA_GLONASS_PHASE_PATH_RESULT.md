# Separate GPS and GLONASS phase paths preserve the shape preference

The two carrier-phase reconstructions agree to **7.0 cm horizontal
RMS** over the later two minutes. They differ by **97.3 cm height
RMS**. Both use only their own constellation's satellites and
observations after the same first earlier position anchor.

| Comparison | Earlier horizontal / height RMS | Later horizontal / height RMS |
| --- | ---: | ---: |
| GLONASS against the original receiver export | 19.2 / 22.9 cm | 34.9 / 59.3 cm |
| GLONASS against GPS carrier phase | 11.2 / 35.4 cm | 7.0 / 97.3 cm |

| Receiver path | Fixed shape score |
| --- | ---: |
| Original receiver export | −6.923 |
| GPS carrier phase | −7.132 |
| GLONASS carrier phase | −6.990 |

Zero is a tie. Both models use the same zero background field.
The globe has the lower forecast error with each path, with the
same working weights, smooth corrections and fitted calibrations.
The GPS and GLONASS scores differ by 0.141 units despite the
height disagreement.

The GLONASS replay completed all **1,038** charged steps on the
same 520 matched reports, using at least seven satellites. The
clock normalization and continuity exclusion record are preserved.
The two constellations have separate satellite signals and broadcast
data. The reconstructions still share the aircraft antenna, initial
position and working atmosphere model. These results test some
constellation-specific errors on one flight. Common error and
independent-flight accuracy remain open. No inertial fit or forecast
propagation ran, and the reserved ESA groups stayed sealed.

## Reproduce the replay

Use the sealed RINEX excerpt, broadcast ephemerides, first earlier
position, clock-step result and [GLONASS continuity inventory](ESA_GLONASS_PHASE_SUPPORT_RESULT.md).
Prepare in a separate reproduction directory with the frozen
environment. For the completed study, use the report command only.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_glonass_phase_path prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-glonass-phase-path-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_glonass_phase_path report
```

[Fixed method](ESA_GLONASS_PHASE_PATH_PLAN.md) ·
[Comparison scores and position differences](esa-glonass-phase-path-result.json)
