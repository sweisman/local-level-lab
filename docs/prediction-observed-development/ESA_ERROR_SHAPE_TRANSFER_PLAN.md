# Test whether two forecast-error shapes extrapolate

Use the two sealed 120-report forecasts and the separate, receiver-screened
400-report straight-flight forecast from ESA recording 187. For each short
forecast use reports 1–90 to estimate a correction and reports 91–120 to
score it. For the straight forecast use reports 1–200 and 201–400.
Keep every report. These are retrospective splits of already scored
flight development data.

Compare four descriptive correction shapes to each original forecast.
Fit a position offset and a velocity offset, add a constant acceleration
term, add a maneuver response, or add both terms. The maneuver response
uses the saved 1°/s angular-motion trigger and the coherent sum of the
existing 15-second decaying acceleration responses. All coefficients are
estimated from the prefix only, separately for north, east and up. Score
RMS position error on the remaining reports. A response that cannot be
estimated from the prefix remains unqualified. The receiver-screened
straight control uses only the state and acceleration corrections.

Use both archived IMU error descriptions on the short forecasts and the
one available description on the straight forecast. Allow at most 18
small linear solves, one numerical thread, no original trajectory fit
starts or native steps, and no protected data reads. These checks use physical position error in
metres. They do not calibrate a covariance, change the frozen forecasts
or supply confirmation independent of this flight.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_error_shape_transfer freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_error_shape_transfer replay
```
