# Receiver acceleration in the three selected training windows

Use the same 800 earlier receiver queries in each of the three
preselected development windows on ESA recording 187. Partition each
into 32 groups of 25 consecutive queries. At the center of each group,
estimate velocity and its derivative with a local quadratic fit over
11 and 25 reports. Use actual GPS timestamps and the printed joint
velocity covariance in north, east and down after converting the sign
of height velocity.

Report acceleration by axis and an estimated force magnitude under the
conventional rotating-globe receiver chart with fixed apparent gravity
of 9.81 m/s². This supplies a calibration feasibility check in an
explicit frame. It makes no comparison of Earth models. Propagate the
velocity covariance to each force magnitude, including the derivative
of the transport and rotation corrections with respect to velocity.
Report a linearized standard deviation for independent epochs and an
upper bound for arbitrary temporal correlations at the printed marginal
covariances. Calculate the spread of the two stencil estimates on the
same centers. Compare both with the 0.001 m/s² working drift scale.

One numerical thread, one original receiver scan, 2,400 selected
training reports and 192 derivative evaluations. No raw inertial data,
later receiver observations or protected groups enter the calculation.
The printed receiver covariance has not been calibrated against true
aircraft motion. The two stencil estimates can also differ because of
actual changes in acceleration. This study does not separate those
causes or supply an absolute prediction-error law.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_receiver_acceleration freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_receiver_acceleration replay
```
