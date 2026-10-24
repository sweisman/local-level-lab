# ESA prediction result: metres versus kilometres

**Three complete comparisons favor globe geometry and the specified background
field.** In this development recording, that model predicts unused positions
with a typical three-dimensional error of about **15 metres**. Zero-field globe
gives **3.8–4.4 kilometres**, and the tested disc **7.4–8.6 kilometres**.

These are comparisons of RMS position errors, not calibrated probabilities.
All three settings reuse **one twenty-minute recording**, rather than three
independent flights.

## What was tested

The recording comes from the ESA airborne survey archive. It contains about
360,000 IMU samples, averages 292.2 km/h and lies near 64.19° N. An **IMU
(inertial measurement unit)** records turning with gyroscopes and specific force
with accelerometers.

Earlier receiver positions determine the initial state and instrument
calibration. The software then predicts later positions continuously from the
IMU record, without using those later positions to adjust the answer. Horizontal
and height errors must both meet the fixed accuracy limits.

The four settings combine two assumptions about upstream background-field
removal with two assumptions about how receiver errors persist in time. Each
setting requires qualified forecasts from all three candidates. Repeated
starting points probe numerical stability; they are not additional flights.

## What improved

Wider computer arithmetic improves numerical completion from **8 to 22 of the
24 starts**, with all eight earlier passes retained. It changes no measurement,
calibration bound, starting point, stopping check or accuracy limit. Independent
generated controls qualified the revised calculation before this run.

The preferred model's later horizontal RMS is **6.8–7.8 m** and height RMS
**13.4–13.7 m**. It passes the physical accuracy checks in all three complete
comparisons. The alternatives' much larger errors remain after their numerical
fits have converged.

Two disc starts in the short-memory, profiled-removal setting reached the
eight-hour cooperative ceiling. That setting remains incomplete. The run used
1,175 native calculations; its saved-results audit repeats no fit or propagation.
Every failure and all charges are preserved.

## What remains

This is development evidence from one recording. The working error assumptions
still need assessment, and statistical confidence has not been calibrated.
Seven separate ESA confirmation groups remain protected. The supplied field
rate does not establish its cause or a solar-versus-sidereal distinction.

The next check examines the saved errors' growth and temporal dependence before
broader prediction tests. The 53-stretch findings remain unchanged.

[Full result tables](README.md) · [Every start](fits.csv) ·
[Matched baseline changes](baseline-changes.csv) · [Execution scope](EXECUTION.md) ·
[Next analyses](../NEXT_STEPS.md).
