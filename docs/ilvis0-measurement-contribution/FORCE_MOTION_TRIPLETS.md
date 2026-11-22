# Can one orientation satisfy both adjacent motion limits?

An accelerometer fixes the direction of specific force in its own axes.
Matching it to the force required by a trajectory still leaves the instrument
free to turn about that direction. A check of two samples can allow an
orientation that conflicts with the next pair. The three-sample check requires
the middle sample to use the same orientation for both pairs.

The calculation first converts each required force vector from local
north, east and down to axes fixed to the candidate geometry. On the globe,
local down turns with the surface normal. On the disc, down stays parallel
and the horizontal axes turn with longitude. The specified background field
affects required force and does not rotate these coordinate axes.

## How the check works

Choose any middle orientation that aligns the two middle force directions.
All other compatible orientations differ by a twist about the required force
direction. At either neighboring sample, measure the angle between its
required direction and its body direction as rotated by the middle
orientation. That angle is the shortest possible additional rotation needed
to match the neighbor. The maximum angular rate times elapsed time gives the
allowed angle for that step.

For each neighbor, the dot product of the two directions is a constant plus
one cosine and one sine of the middle twist. Requiring the dot product to be
at least the cosine of the allowed step gives an allowed arc on the twist
circle. The middle orientation can serve both steps exactly when the two
arcs intersect, within the stated numerical allowance. For uncertain force
directions, the calculation widens each step limit by the direction errors at
both endpoints. Exclusion after widening is a necessary failure under those
declared bounds. A surviving arc leaves the triplet possible under the relaxed
limits. Different triplets can still require incompatible orientations.

## What the controls establish

Nine new deterministic checks cover a case where each pair passes but the
middle orientation cannot satisfy both. They also cover an independently
constructed bounded motion, the exact transition for the counterexample,
unequal time steps, opposite directions and all four geometry and field
combinations. The coordinate basis changes at the transport rate of each
candidate. All 41 new and related tests pass.

The screen uses no gyro or fused attitude. Using it on a flight requires an
independently supported rate limit in the same fixed frame, force-direction
error bounds and one shared accelerometer calibration. A limit stated in the
local navigation frame must first account for that frame's transport. This
check covers sampled directions. Force magnitudes, motion between samples and
whole-history feasibility are separate checks. No aircraft fits were run.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_ilvis0_force_motion_triplets.py \
  analysis/tests/test_ilvis0_force_motion_screen.py \
  analysis/tests/test_ilvis0_gyro_free_path.py \
  analysis/tests/test_ilvis0_channel_controls.py
```

[Implementation](../../analysis/lll/ilvis0_force_motion_triplets.py) ·
[Sensor-channel controls](CHANNEL_CONTROLS.md)
