# The remaining loss is nonlinear and shared

All **48 saved-sector audits pass**. The audit makes 2,592 linear-program
proposals, checks their exact support certificates and retains all 27
calibration coordinates. It performs no native integration or aircraft fits.

Stronger linear projection does not narrow 25 of the 27 parameter ranges in
any sector. Only tiny additional changes occur in two initial-position
coordinates. Orientation, velocity, lever arms, gains, biases and timing remain
at their previous ranges. This diagnoses the supplied conservative enclosure;
it does not show that actual instruments cannot be calibrated.

The saved future widths reconcile with their affine and nonlinear parts.
**Every sector's retained nonlinear height allowance alone exceeds the tenfold
target**, even before adding affine uncertainty. Thus a better linear optimizer
alone cannot make this construction pass. Recomputing a justified smaller
remainder could change that conclusion.

The next candidate preserves errors that are common to a recording. Two
specific examples are an uncertain initial lever/attitude product and the
product of initial velocity error with a common time offset. Counting these
as fresh independent errors at every epoch exaggerates the allowed variation.
They must be separated algebraically, not declared constant because the saved
numbers look similar.

The original 27 physical parameters and their full bounds will remain.
Additional bounded coordinates may represent proven shared remainder terms;
these are a conservative enclosure device, not new physical candidates or
fitted sensor specifications. Native qualification and useful prediction bounds
remain required before new observed work. The 53/0/0 numerical result is unchanged.

[Complete parameter table](README.md) · [Intervals and certificates](parameters.csv) ·
[Frozen audit](PLAN.md) · [Shared-reference design](../ilvis0-shared-reference-native/PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
