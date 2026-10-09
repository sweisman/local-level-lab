# All qualifying high-speed airborne stretches

This extension checks all 232 retained ILVIS0 recordings and preserves every qualifying
stretch. The six-recording refinement is complete, and this extension is running. Screening
found 53 eligible stretches totaling 424.3 minutes; these can overlap across instrument streams.
Earlier evidence and originals remain intact. No calibrated detection is claimed.

An interval must last **240 continuous seconds** after exclusions, with **every associated
receiver ground-speed observation at least 700 km/h**. It must also satisfy:

| Property | Requirement |
|---|---|
| Sampled motion | Full navigation alignment; roll within ±5°; vertical speed within ±1.5 m/s; central course-change rate at most 0.05°/s. |
| Position/speed | Checksummed embedded receiver messages; valid position quality and height/geoid fields; unique speed-to-dated-position association within 0.5 seconds; gaps no longer than 2 seconds. |
| Boundaries | Remove ten seconds at each end of a qualifying motion/speed interval; retain 0.2 seconds of extra raw data for the ±0.15-second timing sensitivity. |
| Raw IMU | Strict framing/checksums; no reported status error; rate code 2; adjacent intervals of 2.5–7.5 ms; unchanged IMU type, time basis and logged installation signature. |
| Timing | Dated embedded receiver UTC reproduces packet timing. Unsupported timing is recorded, not repaired. |

Fused navigation screens aircraft motion only; it is never an independent Earth-model
observation. Sampled limits do not rule out tiny aircraft corrections. No gyro residual or
preferred model determines selection. Ground speed is neither true airspeed nor a flight
average. Geometry eligibility is separate from supported decoding, convergence and model
information.

## Permanent selection record

Before extension fitting, the worker saves the complete technical selection and publishes:

- `eligible-stretches.csv`: stable stretch identifier, original filename/SHA-256, exact UTC
  start/end, duration, minimum/median receiver ground speed, IMU type, mounting epoch,
  policy version and selection fingerprint.
- `files.csv`: all retained files, including exclusions and unresolved context with reasons
  and nonexclusive rejection counts. Byte-identical aliases reference their canonical file.
- `ELIGIBILITY.md`: plain-language criteria and selected totals.

These are now published, before fitting finishes. They are generated from
the frozen selection, so publication and later analyses need not recalculate intervals.
Changing the rules requires a new version. Different instruments on the same flight may
overlap; recording counts and minutes are not counts of independent flights.

## Analysis and recovery

Each complete stretch is fitted jointly without a ten-minute primary limit. Fixed four-to-ten
minute sections check residuals at the same parameters; they are not separately fitted decisions.
Known gaps/configuration changes split stretches. Joining files requires verified continuity.

Two primary sensitivity cases use the same **±1 degree/hour constant gyro-offset allowance**:

| Case | Assumed processing of the recorded gyro increments |
|---|---|
| No Earth-rate removal | Removal is fixed at zero. |
| Possible Earth-rate removal | A shared removal fraction is fitted between zero and one. |

Published noise and system drift figures do not establish the remaining calibration offset
or processing of each archived recording. These cases are hypotheses, not measured drift or
verified per-unit bounds. The tighter ±0.1 degree/hour sensitivity is deferred for the extension;
the completed six-recording refinement retained all four cases. Other error limits and assumed
correlated receiver covariance match that refinement. Time-varying calibration errors are not
added in this pass.

All three models are fitted together under each case: flat disc, still globe and rotating globe.
The first reported question is **globe, flat or unknown**, comparing the flat fit with the better
globe fit. Rotation results are exposed only when all required fits converge and both cases
favor the globe. This reuses the globe fits; a separate rotation fit is unnecessary. Results
remain conditional on these assumptions. Calibrated scientific decisions remain abstain.

At launch, source/input/environment hashes are frozen. After inventory, a second manifest
freezes identities and the finite allowance: N stretches permit 6N primary starts plus 2N
interruption retries, at most two starts per identity and 200 total evaluations per start.
Interrupted starts stay charged; verified selections/results are reused. Exclusive locks,
fsynced journals and atomic hashed outputs support recovery. At most two numerical threads;
no synthetic campaign or original deletion.

Code: `analysis/lll/ilvis0_segments.py`; runner: `analysis/tests/ilvis0_segment_worker.py`.
Output: `data/ilvis0-highspeed-segments-v2-20261008/`; matching `.log` beside it.
The superseded four-case extension was stopped while queued, before inventory or any fit start.
Its original freeze remains preserved; it must not be resumed. The geometry-selection policy
is unchanged; only the fit-case grid and its separately frozen run have changed.
Check lock/status before resuming an unfinished, unchanged freeze. Completed studies never
resume. To regenerate public evidence after completion without scans or fits:

```sh
env PYTHONPATH=analysis OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 /home/sweisman/venv/bin/python analysis/tests/ilvis0_segment_worker.py --package-only
```

See the [general methodology](../METHODOLOGY.md) and
[instrument/refinement assumptions](../ilvis0-refinement-20261008/README.md).

## Public results summary

The [pilot findings](../ilvis0-refinement-20261008/PROVISIONAL.md) are available now.
The [final summary](FINAL_SUMMARY.md) will compare convergence by model and processing case,
fully converged versus unresolved stretches, residuals, parameter limits and conditional
shape/rotation outcomes. The separate `summarize_results.py --watch` waits for audited
publication and reads only saved results; it does not scan original recordings or run fits.
To regenerate that summary after completion, run the script without `--watch`.

The detailed stretch ledger will include original filename/hash, Group-4 record type and
logged IMU type, UTC bounds, duration, minimum/median receiver ground speed, approximate
horizontal track distance, mounting epoch and conversion information. A separate track CSV
will retain every selected receiver position without interpolation. The distance uses a
declared spherical coordinate convention for description, never as evidence about Earth shape.
For indeterminate results, matched globe/disc pairs are described only when both fits converged;
unfinished costs remain diagnostics. Partial leans do not promote the primary shape decision
or expose rotation when the complete shape comparison remains unresolved.

## Review after the frozen run

First compare convergence with duration, receiver ground speed, IMU type, installation
and route geometry. Use the number of converged fits per stretch as well as whether all
six converged. Describe correlations without treating overlapping stretches or repeated
instrument recordings as independent trials. The completed subset during execution is
ordered by source date, so its relationships need not describe the final selection.

Then separate numerical difficulty from scientific separation. Review stopping messages,
stationarity, parameter-limit hits, residual patterns and poorly constrained parameter
combinations. Check whether solver scaling, initialization or parameterization can improve
convergence while preserving the same physical model. Review calibration and processing
assumptions against available instrument evidence, and test their effects equally across
all Earth models. Faster travel strengthens the curvature scale, but neither speed nor
duration guarantees convergence or useful separation from instrument errors.

This completed study remains preserved. Any revised fits require a new identified
development configuration and finite approved compute scope. Reuse the saved intervals;
do not tune selection boundaries or assumptions to favor an Earth model. Improvements
chosen using these results are development findings and require separate validation.
