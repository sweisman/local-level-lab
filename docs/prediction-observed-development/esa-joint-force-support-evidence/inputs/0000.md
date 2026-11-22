# Apply one force calibration to the earlier and later scores

The [earlier GPS check](ESA_LINKED_TRAINING_SUPPORT_RESULT.md) allowed the
nine shared force coefficients to vary independently. Reuse its six
saved directions and exact multipliers. For each, subtract the projected
earlier coefficient from the corresponding later coefficient before
bounding the force transform. The combined coefficient then multiplies
one physical rotation and gain map throughout the recording.

Keep the earlier allowance, standardized error scenarios and all other
coefficients unchanged. Reproduce the independent-box result exactly
before replacing its nine force terms with the physical bound. Use its
original value if subdivision fails to tighten it. Per candidate, allow
three force bounds of at most 63 box evaluations and 40 seconds of
subdivision each. Run two one-thread workers with a cooperative
150-second total allowance. Start no fits and read no unused receiver
observations or reserved recordings.

The result still relies on a hypothetical earlier unshared error limit,
leaves later unshared error outside the calculation and uses a working
covariance. It cannot qualify aircraft prediction coverage.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- \
  env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_joint_force_support
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies run \
  data/esa-joint-force-support-v1-20261119 --reserved-threads 0
```
