# What receiver samples can establish about aircraft motion

The ESA development recording has some quiet position-derived trends, but no
qualifying continuous stretches yet. A fitted trend is not a measurement of
every movement between receiver samples. Even perfect position and velocity
samples cannot establish that instantaneous course changes stayed below a
small cutoff unless additional motion assumptions are supplied.

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

The current ESA adapter constructs component integrals under explicit sampling
hypotheses. It does not yet qualify complete finite rotations, coning/sculling
or geographic uncertainty propagation. Those requirements remain open; this
example does not establish that a less restrictive selection is ready.

Recording 187 remains development material. The zero-eligible version-1 inventory
and all earlier diagnostics are preserved, and the seven confirmation groups
remain protected. No new receiver inventory or Earth-model fitting is performed
by this analysis.

[Completed receiver assessment](esa-position-assessment/INTERPRETATION.md) ·
[Selection proposal](external-imu-data/ELIGIBILITY_PLAN.md) ·
[Current receiver-only rule](../analysis/lll/airquantumgrav_selection.py) ·
[Rate-input adapter](../analysis/lll/airquantumgrav_increments.py) ·
[Local body bounds](../analysis/lll/airquantumgrav_body_bounds.py) ·
[Roadmap](ANALYSIS_ROADMAP.md).
