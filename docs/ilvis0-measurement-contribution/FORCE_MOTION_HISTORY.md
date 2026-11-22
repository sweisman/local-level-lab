# Can one gyro-free orientation path fit all sampled force directions?

Yes for some force histories. Other histories have no compatible orientation
path under a stated motion limit, even when every three-sample check passes.
The whole-history check follows the allowed rotations from the first sample
to the last and can return a path, prove an exclusion at its stated bounds,
or leave the question open at the chosen resolution.

## How it works

At each sample, the force directions leave one free angle. Put an equally
spaced grid on that angle and track which grid points can follow a reachable
orientation at the previous sample. Each previous orientation permits an
arc of next angles. Combining arcs takes work proportional to the grid size
per sample and avoids building a matrix of all possible transitions.

The calculation runs two searches. The first adds one grid spacing to each
allowed turn, covering the worst-case error from rounding both endpoints
to nearby grid points. It also adds the declared force-direction errors at
both endpoints. If even this enlarged search loses all paths, no continuous
choice of the sampled angles can meet the stated bounds. The second search
uses the original step limits and nominal force directions. It returns a
path only after checking every direction and turn directly. A path in the
enlarged search alone leaves the result open. The software reports the
grid spacing and allows a small floating-point tolerance at cutoffs.

## What was checked

The constructed four-sample counterexample passes both overlapping triples,
but the whole-history check excludes it. A coarser grid leaves the same
example open. A separate construction returns a path that an independent
rotation calculation verifies. The fast arc transitions also match direct
quaternion comparisons on the tested grids. All 47 new and related checks
pass. One generated stress check covers 1,500 samples with 1,024 angles per
sample and returns a verified path in under one second on one local thread.

This checks sampled directions for fixed calibration and required forces.
It does not bound force between samples or establish the unknown aircraft
attitude. Recorded use requires defensible direction errors, a motion limit
independent of the omitted gyro, and treatment of shared calibration and
receiver uncertainty. No aircraft fits or archive decisions were run.

The [recorded check](RECORDED_MOTION_RATE_RESULT.md) keeps both GPS paths,
both clock conventions, the fixed training split and all four candidates.
The four candidates' rate brackets overlap in every matched setting.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_ilvis0_force_motion_history.py \
  analysis/tests/test_ilvis0_force_motion_triplets.py \
  analysis/tests/test_ilvis0_force_motion_screen.py \
  analysis/tests/test_ilvis0_gyro_free_path.py \
  analysis/tests/test_ilvis0_channel_controls.py
```

[Implementation](../../analysis/lll/ilvis0_force_motion_history.py) ·
[Three-sample check](FORCE_MOTION_TRIPLETS.md) · [Channel controls](CHANNEL_CONTROLS.md)
