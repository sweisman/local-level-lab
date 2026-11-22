# Prepare the four ESA steady-course controls

Use the [four verified clock windows](ESA_STRAIGHT_CONTROL_PLAN.md) on
development recording 187. Save the same three files for each window as
in the repeat-turn study. These contain 400 earlier GPS positions,
the complete query clock and inertial increments. Preserve the 120
later positions separately. Check the original source hashes and
the clocks before packaging.

Use a single pass to verify each original file, the same linear-point
inertial conversion and margin for the sensor time offset, and the
original per-window limit of 157,000 samples. Record when angular
motion exceeds the earlier threshold. Stage at most 48 MiB of files.
Allow one worker on one numerical thread up to ten minutes. Run zero
fits and open no reserved recording.

The tests verify the original clock receipt and reject unexpected
later-position inputs before accessing the study files. Prepare the
study without using a numerical slot. Run it only when a slot is free.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_straight_control_material request
env PYTHONPATH=analysis PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ~/venv/bin/python -m pytest -q \
  analysis/tests/test_esa_straight_control_material.py analysis/tests/test_esa_straight_control_windows.py \
  --junitxml=docs/prediction-observed-development/esa-straight-control-material-tests.xml
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_straight_control_material prepare
```

After preparation, the one task runs through the numerical guard and
the shared `lll.studies run` command with
`data/esa-straight-control-material-v1`. The separate forecast study
needs its own qualified fit and recovery limits.
