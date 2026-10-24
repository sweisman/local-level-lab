# Investigating prediction accuracy

The completed, audited globe-with-field fits satisfy the training accuracy screens,
but later horizontal RMS is about 21–27 m and height RMS is 168–212 m. The fixed
limits are 10 m and 30 m. The [saved-data diagnosis](../esa-development-diagnosis/README.md)
preserves those forecasts and adds no fit or propagation.

Nine of twelve model/settings forecasts are available. Calibration still reaches
bounds. The declared radial-gravity sensitivity varies by 0.00629 m/s² across
the height range, with an illustrative 187 m position scale. This is a hypothesis
worth testing, not measured gravity or proof of the forecast error's cause.
No confirmation data has been released.

## First verify, then diagnose

The completed audit verifies every source, input and artifact hash, charge,
training/forecast boundary and physical error. Preserve all starts and failures.
Select each primary by training cost alone, including retaining a failed forecast
from the best training start rather than switching to an alternative.

Then use the saved interval and forecasts for a separately bounded diagnosis:

1. **Check repeatability.** Compare both starts' calibration and later errors.
   Agreement supports numerical repeatability; it does not establish a global
   optimum, unique calibration or a correct observation model.
2. **Locate error growth.** Plot north, east and height errors across training
   and prediction, alongside the recorded height, speed and course. Look for
   steps, slopes and curved growth without changing the forecast or its score.
3. **Inspect calibration.** Report normalized parameters and boundary proximity,
   especially gyro bias/gain, accelerometer bias/gain, gravity and latency.
   Keep initial-state error, constant offset and changing drift distinct.
4. **Examine the gravity approximation.** Both native kernels currently use one
   fitted gravity magnitude for the interval. The selected path spans roughly
   1,483–3,526 m in height. Assess whether a physically plausible change in
   gravity could explain the scale and direction of the height errors.
   Do not treat accelerometer magnitude as gravity during aircraft motion or
   infer a measured gravity law by correcting the scored position residuals.
5. **Check timing and initialization.** Reconcile actual sample times, latency
   support, initial force-based gravity and the saved training prefix. Do not
   open a new timing search or retry the existing starts.

Saved-data inspection must not invoke the motion kernels, refit calibration,
replace omitted measurements or reopen original or protected recordings.
If a diagnostic needs new propagation, it requires a separate source freeze and
finite allowance. The pilot is closed and its thread allocation has been released.

## Any revised model needs its own qualification

If the diagnosis supports changing gravity treatment or another physical
assumption, first test it against independently generated long trajectories
with turns, climbs and the declared error processes. Retain constant-gravity
controls as well as varying-gravity controls, all three physical candidates,
both processing assumptions and all calibration columns. Do not give one
candidate extra freedom or relax the existing accuracy targets.

The independent generator and predictor must not share the implementation being
tested. A common altitude-dependent gravity sensitivity, if justified, must be
declared before fitting and applied consistently across candidates; importing
a preferred geometry's gravity law is not independent curvature evidence.

Only qualified software can enter a separately frozen observed comparison.
Reuse the preselected interval and keep this first pilot intact. Its unused
allowance cannot fund new starts. Exact device documentation remains supporting
work, and seven ESA confirmation groups remain protected.

[Bounded saved-data study](../esa-development-diagnosis/PLAN.md) · [Active fitting plan](FIT_PLAN.md) · [Pilot status](README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
