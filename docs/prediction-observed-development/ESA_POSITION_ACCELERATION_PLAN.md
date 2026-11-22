# Compare position and velocity estimates of aircraft acceleration

Use the same 2,400 training reports and 96 centers as the
[sealed velocity comparison](ESA_RECEIVER_ACCELERATION_RESULT.md).
At each center fit a cubic to 11 and 25 receiver positions with the
existing local polynomial derivative code. Fit in a locally scaled
receiver chart, then use the full moving-metric kinematics to get
specific force under the same chart and 9.81 m/s² gravity convention as
the velocity calculation.

Propagate all position covariance terms to the force magnitude. Report
the linearized standard deviation under independent reports and its
upper bound under any temporal correlation at the reported marginals.
Compare the two position supports and the position-versus-velocity
differences at the corresponding supports. Use 0.001 m/s² as the working
scale marked in the previous check. Report actual disagreement so that
small propagated covariance alone cannot qualify the method.

Allow one receiver scan, 192 cubic derivative fits, one numerical thread,
zero inertial measurements, zero reconstructed trajectory fits and zero
later or reserved receiver observations. Both inputs come from the
same GNSS solution. Agreement cannot establish independent accuracy.
The comparison also cannot isolate measurement error from polynomial
truncation or a change in the physical motion being averaged.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_position_acceleration freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_position_acceleration replay
```
