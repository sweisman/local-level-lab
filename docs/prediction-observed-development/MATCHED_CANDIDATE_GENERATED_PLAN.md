# Next development gate: one recording, three candidate forecasts

## Question

When the **same** generated IMU increments and earlier receiver positions are
given to all three Earth-model candidates, do their later forecast ranges
separate enough to answer the shape question? A range that covers the correct
route but also covers every competing route is useful for prediction and
uninformative for model discrimination.

This is generated-data development only. It will not open the seven reserved
ESA groups or change any completed result.

## Method and order

1. Generate one synthetic recording and save its raw-input and earlier-receiver
   hashes **once**. Fit rotating globe, stationary globe and stationary disc to
   those exact bytes with the same calibration box, receiver policy and
   26-column nuisance model. Candidate-specific geometry may change the
   predictions, but cannot change the input measurements.
2. Save the point forecast and both target-specific bounds for all three
   candidates before generating or opening later truth or later receiver
   measurements. Bound the **whole withheld path**: assign 0.025 to the shared
   calibration event and divide a second 0.025 across all `3 × future_epochs`
   coordinate errors. The nominal 95% joint claim applies only under the
   declared affine Gaussian error and in-box calibration assumptions.
3. Generate later receiver errors from the same seeded receiver process. Check
   that its earlier prefix exactly reproduces the training receiver data.
   Score coverage and the full width of each candidate range. Count a failed
   fit, missing bound or unusable range as a failure, not as an abstention that
   disappears from the denominator.
4. Report whether a range excludes the flat candidate while retaining at
   least one globe candidate. Report the rotating-vs-stationary globe contrast
   only after shape. The result remains descriptive and scientifically
   undecided until independent coverage and the aircraft error law qualify.

## Finite development matrix

First run one 10-second source-bound preflight with one generating model and
all three candidate fits. Qualify task-level recovery with an interrupted
worker test before launching a longer run.

If the preflight passes, use twelve 120-second synthetic recordings: each of
the three generating models at 55° N and 55° S under both declared IMU error
laws. Use distinct fixed seeds for every recording. The north and south cases
use climb and descent profiles respectively. Each recording has 119 receiver
epochs, split into earlier training and later scoring by the existing shared
split rule. Fit all three candidates per recording with at most 200 evaluations
per fit and no extra starts. That is **36 candidate fits**. Reserve all native
operator passes and packet visits before execution, use two one-thread workers
and a finite three-hour wall cap. No allowance is expanded after launch.

This matrix tests wiring, route transfer and descriptive separation. Twelve
recordings, some sharing geometry and construction code, cannot calibrate
95% whole-flight coverage or a false-rejection rate. Any later confirmation
study needs new routes/seeds, an exact sample-size calculation, and a
predeclared width/selection rule. The inherited 0.1 m clean-data path screen
remains historical; noise-aware physical adequacy is reported separately.
