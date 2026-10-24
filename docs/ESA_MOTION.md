# What receiver samples can establish about aircraft motion

The current full-motion selection admits two ESA development runs totaling
393.4 minutes. The earlier quiet-flight policy admitted none. This page explains
why quiet receiver trends alone could not satisfy that earlier requirement,
and why the project instead qualified a calculation that handles aircraft motion.

A fitted trend does not measure every movement between receiver samples.
Even perfect position and velocity samples cannot establish that instantaneous
course changes stayed below a small cutoff without additional motion assumptions.

The version-1 selector screens a ten-second median of sampled course-rate
estimates. That statistic and an instantaneous-motion guarantee are different
requirements.

This is a sampling limitation, not evidence of poor instruments or a claim that
the aircraft actually made the unobserved movements in the example below.

## An exact example

Consider receiver samples every half second and forward speed 50 m/s. Compare a
straight path with the same path plus a small sideways movement within each
sample interval. With interval length Δ and normalized time u between zero and
one, define the sideways displacement as:

\[
y(t)=A\,u^2(1-u)^2,\qquad u=(t-t_i)/\Delta.
\]

At both ends of every interval, the added displacement and velocity are exactly
zero. Both paths therefore give identical receiver position and velocity samples.
Their sampled course and fitted course trend are identical too.

Yet the second path has acceleration \(2A/\Delta^2\) at those endpoints. Its
instantaneous course rate there is \(2A/(v\Delta^2)\) radians per second.
For A = 0.004 m, Δ = 0.5 s and v = 50 m/s:

- The largest sideways displacement is A/16: **0.25 mm**.
- Endpoint sideways acceleration is **0.032 m/s²**.
- Endpoint course rate is approximately **0.0367°/s**, above the **0.02°/s**
  quiet-course cutoff, despite identical sampled positions and velocities.

Repeating this polynomial gives continuous position, velocity and acceleration;
the ambiguity does not depend on a position jump or a missing receiver epoch.
Reducing receiver noise alone cannot remove a movement that leaves its samples
unchanged. A physically justified acceleration, jerk or bandwidth restriction
could rule out particular examples, but that restriction is extra information.

## Consequence for the ESA study

There are two valid development paths:

1. **Keep the quiet-flight requirement.** Specify and justify the additional
   between-sample motion bound, propagate receiver uncertainty and screen every
   required interval. Sparse quiet trends alone cannot certify it.
2. **Qualify the complete motion treatment.** Demonstrate that the rate-input
   adapter and navigation calculation correctly handle the relevant maneuvers,
   sampling hypotheses and timing uncertainty under all three physical candidates.
   A new receiver-only selection can then use the demonstrated capability domain.

The ESA adapter constructs component integrals under explicit sampling hypotheses.
Its [geographic qualification](esa-geographic-rate-controls/README.md) now passes
all 72 generated twenty-minute maneuvering cases, using independent analytic
trajectories and all three physical candidates. With linear point samples,
maximum position error stays below 10 cm. Holding each sample constant gives
much larger errors despite passing the required refinement checks.

That result first qualified the tested calculation with known initial state and
zero antenna offset. The [24-case extension](esa-observation-controls/README.md)
also passes with known sensor errors, antenna offsets and perturbed starting
conditions; maximum position error stays below 10 cm when the correct adjustments
are supplied. The [training-only extension](esa-training-forecast-controls/README.md)
also passes all 24 fits: it estimates calibration from earlier observations and
predicts later positions on noiseless generated two-minute tracks.

Neither result establishes the instrument's actual sampling or filtering
behavior. Two [working receiver-error cases](ESA_ERROR_POLICY.md) are now defined
and software-checked; their coverage remains uncalibrated. The [revised inventory](esa-development-selection-v2/README.md)
now admits two runs totaling 393.4 minutes. It reads receiver observations only,
without gyro-based selection. The [first interval](esa-development-pilot-preparation/README.md)
is now prepared. All 48 [matched weighted controls](esa-weighted-training-controls/README.md) pass,
and the separately frozen [observed pilot](esa-development-pilot/README.md) is complete.
Fifteen of 24 starts pass numerical checks. The one complete three-model comparison
has lower error for globe geometry but fails prediction accuracy; no successful
replication is established. The [saved-data diagnosis](esa-development-diagnosis/README.md)
is complete. All 48 [independent gravity controls](esa-gravity-controls/README.md)
pass with known corrections; all 24 [training-only cases](esa-height-training-controls/README.md)
also qualify. The [observed gravity revision](esa-observed-height-pilot/README.md)
now completes one adequate three-model setting, using the same original interval,
calibration bounds and physical-accuracy limits. Eight of 24 fits pass numerical
checks; the qualified specified-field forecast has 6.80 m horizontal and 13.71 m
height RMS on later observations. Stopping failures remain for other settings.
The generated controls read no original recording or protected observation.

Recording 187 remains development material. The zero-eligible version-1 inventory
and all earlier diagnostics are preserved, and the seven confirmation groups
remain protected. The inventory and observed pilot are separate frozen studies;
their original limits and failed results remain preserved.

[Completed receiver assessment](esa-position-assessment/INTERPRETATION.md) ·
[Selection proposal](external-imu-data/ELIGIBILITY_PLAN.md) ·
[Current receiver-only rule](../analysis/lll/airquantumgrav_selection.py) ·
[Rate-input adapter](../analysis/lll/airquantumgrav_increments.py) ·
[Local body bounds](../analysis/lll/airquantumgrav_body_bounds.py) ·
[Roadmap](ANALYSIS_ROADMAP.md).
