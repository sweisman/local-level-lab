# Separate smooth position errors from the remaining variation

Use only the four [turning windows](ESA_REPEAT_TURN_FORECAST_RESULT.md) and
four [steady windows](ESA_STRAIGHT_CONTROL_RESULT.md) already scored on
development recording 187. Retain both inertial error descriptions for
each window. Verify both releases, all 16 forecast seals and the archived
scores before reading any GPS positions. Reuse the original receiver clock
and position conversion. Check that the original combined score is reproduced.

In each three-axis position error, measure the component representable by
a constant, a linear time trend and a quadratic time trend. These correspond
to a shift in position, velocity and acceleration over the prediction period.
Whiten the error and these fixed terms with the same full covariance used
for scoring. Project onto the nine terms together. Record the original,
projected and remaining squared errors, their dimensions and the projected
position error at the last report. Use the combined steady and turn
covariance in every window.

This retrospective check allows terms estimated from the later errors, so
the projected component cannot be used to correct an actual withheld
forecast. Smooth residual patterns can arise from a drifting predicted
path, correlated receiver error or a poorly specified covariance.

Use one numerical thread and at most 16 small projections. Decode only
the 960 already scored GPS reports. The diagnostic starts no trajectory
fits and reads no reserved recording. The source and receipt freeze is
`esa-scored-path-shape-freeze.json`. Run both commands from the repository
root with the same numerical guard.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_scored_path_shape freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_scored_path_shape calculate
```
