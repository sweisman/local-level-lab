# Compare receiver and IMU force over the same time support

Keep the 96 sealed training centers and their 25-report position
fits from the [position comparison](ESA_POSITION_ACCELERATION_RESULT.md).
The linear second-derivative weights give an exact time kernel for
averaging acceleration over each receiver support. Use that kernel to
average two force magnitudes: the logged acceleration magnitude and
the magnitude required by the same cubic receiver trajectory. Compute
the magnitude before averaging on both sides, so changing axis direction
does not manufacture a difference from the averaging order.

Use left-held values of original iMAR point samples within each support.
Compare the fitted path at two numerical quadrature orders. Use the same
conventional receiver chart, background field and fixed apparent gravity
of 9.81 m/s² as the earlier receiver estimates. Keep all three windows.
Compare their raw force differences and transfer a single descriptive
median offset from the other two windows to each window in turn.

The bounds are one hash pass over each source, 2,400 earlier receiver
reports, at most 723,000 decoded IMU samples, 96 derivative kernels,
two quadrature orders and three scalar offsets, on one numerical
thread. The work uses no later receiver outcomes, reserved files, fused
attitude, numerical trajectory fits or native propagation.

Matching time weights cannot restore motion removed by the receiver
polynomial. The comparison leaves gravity-model error, sensor calibration,
latency, acceleration at the different IMU and antenna locations, and
receiver errors unresolved. The windows are from one flight and the
offset-transfer exercise cannot validate independent prediction coverage.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_matched_force freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_matched_force replay
```
