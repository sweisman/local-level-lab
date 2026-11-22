# Prepare the new ESA solver comparison

Use the [verified 20-minute window](esa-dispatch-clock-result.json) on
development recording 187. Both solver implementations will use the
same 800 GPS training positions and forecast at the same 400 later
times. Keep the later measured positions outside the prepared files.

Read the original receiver export once, checking its hash and the
previously verified clock. Decode positions only at the training
indices. Verify the inertial recording hash and decode at most 362,000
rows within the checked window. Use the same linear interpolation
between logged inertial samples and the same training weights as the
earlier solver comparison. Check that the input covers the full sensor
time-offset allowance of ±0.01 s.

Preparation uses one worker and one numerical thread, with a five-minute
wall limit and at most 32 MiB of prepared artifacts. It makes no fits and
opens no reserved recording. The paired comparison and its judgment
require a separate freeze.

The tests check the clock and packet limits and give the receiver reader
invalid later position fields. It must still decode the earlier GPS
positions and return all the scheduled query times. The following
commands qualify and freeze the preparation job from the repository root.
They do not launch the job or read the original recordings.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_dispatch_inputs request
env PYTHONPATH=analysis PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ~/venv/bin/python -m pytest -q \
  analysis/tests/test_esa_dispatch_clock.py analysis/tests/test_esa_dispatch_window.py \
  --junitxml=docs/mixed-tangent-hybrid/esa-dispatch-inputs-tests.xml
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_dispatch_inputs prepare
```

When no other numerical jobs are active, launch the frozen preparation.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-dispatch-inputs-v1 --reserved-threads 0
```
