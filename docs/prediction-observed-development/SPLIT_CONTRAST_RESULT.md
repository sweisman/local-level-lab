# Choose forecast directions before estimating their error

In a generated control, choosing the forecast direction from a separate
earlier window kept the directional and remaining errors close to their
nominal 95% reference bands. Using the same data to choose the direction
and fit the forecast put **215 of 512** directional scores above the upper
limit, even though the underlying Gaussian error law was correct.

| Condition | Directional error inside band | Remaining error inside band | Directional error above band |
|---|---:|---:|---:|
| Separate direction-selection and fitting windows | 479/512 | 473/512 | 18/512 |
| Reuse fitting data to choose the direction | 297/512 | 403/512 | 215/512 |
| Separate windows with extra later error | 206/512 | 44/512 | 302/512 |

The first window chooses the direction. Independent innovations in the
second window estimate calibration and the common error scale. The third
window supplies the score. The calculation carries fitted calibration
uncertainty into the later residual, then measures error along the chosen
direction and in the remaining directions. Under the fixed affine
Gaussian model the two scores have individual F reference distributions.
They share an estimated scale, so a joint decision needs its own rule.

All three predeclared software checks passed. The dense check also
reproduced the affine calculation with temporally correlated errors.
The stress test deliberately makes the forecast sensitive to parameters
chosen earlier. Its failure rate is a demonstration of data reuse, not
an estimate for actual flights.

The split uses fewer observations to estimate the calibration and can
leave some later directions unidentifiable. Aircraft use also needs to
address nonlinear fitted paths and changes in error after the cut. This
control opened no aircraft data.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.split_contrast_control replay
```

[Fixed design](SPLIT_CONTRAST_PLAN.md) ·
[Frozen inputs](split-contrast-freeze.json) ·
[Full control counts](split-contrast-result.json)
