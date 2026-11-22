# Verify the matched forecasts across the four preselected NASA groups

Build one table from the [fixed four-group selection](MATCHED_PILOT_CANDIDATES_RESULT.md).
Use the [first two-recording preflight](MATCHED_OBSERVED_NUMERICAL_RESULT.md),
the [separately recovered unstarted IMU21 fit](MATCHED_UNSTARTED_DISC_RECOVERY_RESULT.md),
and the [two added groups](MATCHED_EXTENSION_FORECAST_PLAN.md). Preserve the
original IMU8 stopping failure. Give every group one row even when a
shape comparison remains unavailable. All groups are retrospective
development cases from southern latitudes.

Replay the saved training prefix, later errors and evaluation charges
using the original positions, split, clock and weights. Use the same
inertial forecasts and rerun no fits or propagations. Report relative
shape rankings for each matched field, then a globe field ranking only
if both shape comparisons favor globe across the three GPS tracks.
Keep horizontal and height errors separately alongside the 3D error.
None of the GPS tracks is a statistically separate flight.

Apply the archived NASA descriptive screen to each forecast and each GPS
track. The limits are 10 m horizontal RMS, 30 m height RMS, 50 m maximum
horizontal error and 150 m maximum absolute height error. Also report
signed mean errors and errors over successive 30-second periods. These
periods describe error growth. The screen does not establish calibrated
coverage or the cause of an angular field.

The reporting pass reads sealed fits and forecasts only, makes zero new
starts or propagations and uses one numerical thread. It can first verify
the two closed groups while the two new groups finish. In that release,
the running groups have a pending disposition and no inferred scores.

Run the report after the numerical workers release a thread. Use
`--existing-only` to replay the two earlier groups without writing the final
report. Omit that flag after the eight-fit study seals. The final report
includes one disposition for every planned fit and checks the original
completion and source hashes.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_four_group_audit
```

If the forecast study is interrupted, inspect its original leases and
charges before starting recovery. Reuse the same continuation directory
after the first recovery preparation. The qualification request, test
report and limits are bound to the original study's manifest.

```sh
~/venv/bin/python analysis/status.py --study data/ilvis0-matched-extension-forecast-v1 --recovery
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume close-original --parent data/ilvis0-matched-extension-forecast-v1 --qualification-request docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json
env PYTHONPATH=analysis ~/venv/bin/python -m lll.studies.task_resume prepare --parent data/ilvis0-matched-extension-forecast-v1 --output data/ilvis0-matched-extension-forecast-v1-continuation --qualification-request docs/prediction-group-transfer/observed-fixed-timing-recovery-request.json --max-attempts-per-task 2 --max-technical-interruptions 2 --maximum-wall-s 5400 --minimum-free-bytes 1073741824
env PYTHONPATH=analysis LLL_STATUS_ALLOCATIONS_ONLY=1 ~/venv/bin/python -m lll.studies.task_resume resume --output data/ilvis0-matched-extension-forecast-v1-continuation
```

The closure and preparation steps apply only to an unlocked interrupted run
with unfinished tasks. A sealed scientific failure stays in the original
evidence. Bind any recovered forecast to its separate stage receipt before
adding it to the four-group summary.
