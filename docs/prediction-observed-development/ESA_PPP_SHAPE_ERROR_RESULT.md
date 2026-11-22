# The three processed receiver exports agree in the shape score

The two alternate precise point positioning (PPP) exports moved the fixed
ESA shape score by only **+0.030** and **−0.029** units. The original export
scored **−6.923**, with a tie at zero. All three use the same 400 earlier
and 120 later times on development flight 187, and all favor the zero-field
globe over the zero-field disc in the fixed comparison.

| Export compared with `air1` | Score change from the recorded position match | Score change after time correction | Largest absolute change in the fast-window probe |
| --- | ---: | ---: | ---: |
| `mosaic03` | +0.024 | +0.030 | 0.376 |
| `pwrpak7` | −0.040 | −0.029 | 0.317 |

The largest time mismatch on the fixed comparison was **0.62 ms**.
The time correction uses each alternate export's reported velocity.
Changing the earlier positions affected the corrected score by less
than 0.00015 units for either export. The larger relative changes came
from the 120 later positions.

As a separate check of timing, the fixed weights were applied to the
receiver differences across the previously selected fast windows. Each
export supplied **188 complete windows** with 120 later and 400 preceding
matches per window. Seven others overlapped the fixed shape comparison and
were excluded as planned. The 95th percentiles of the absolute probe
scores were **0.174** and **0.142** for the two alternate exports. The
windows share one flight and can overlap during their earlier portions.
The transferred weights measure the time pattern of receiver disagreement.
They do not compare the two shape forecasts on those other windows.

This is a check of the differences between processed receiver solutions.
The three receivers used one antenna and may share processing errors.
Their agreement leaves common receiver error and future-flight prediction
uncertainty open. No inertial fit or forecast propagation was run, and the
protected flight groups remained sealed.

## Reproduce the comparisons

Use the verified source exports from recording 187, the saved fast-window
inventory and the archived matched-field shape score.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_ppp_shape_error freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_ppp_shape_error calculate
```

[Fixed method](ESA_PPP_SHAPE_ERROR_PLAN.md) ·
[Frozen sources and inputs](esa-ppp-shape-error-freeze.json) ·
[Scores and all window dispositions](esa-ppp-shape-error-result.json)
