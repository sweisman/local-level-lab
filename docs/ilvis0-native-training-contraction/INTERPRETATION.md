# Correct contraction, but prediction ranges remain too wide

All **six generated identities pass the correctness checks**, under three models
and both processing cases. The known true parameters survive both training-noise
assumptions, and every future truth remains inside its calculated latent-position
range. No physical limit or nuisance coordinate was removed.

However, **only two of 27 coordinates narrow**. After 1.5 seconds of generated
training observations, the 1.8-second future ranges still span roughly
**770 m north, 174–596 m east and 512–522 m in height**. Even a declared
1 mm training allowance does not make the complete broad-box calculation useful
for model discrimination. These are overly broad calculated ranges, not measured
aircraft errors or survey-IMU drift.

The test shows why a small box around a fitted answer cannot simply replace the
full region. Initial orientation, lever arms and other calibration possibilities
remain coupled; bounding them separately loses information. Further work needs
to preserve more of that joint structure or establish stronger training-feasible
constraints. Another observed prediction fit does not follow from this result.

The declared arithmetic allowance is also not a global numerical certificate.
The shared receiver-error assumptions and absolute withheld adequacy remain
open. The original 53 numerical comparisons are unchanged.

The sealed study used 30 native calls, 21,600 reserved bound steps and 51.60
seconds, with zero archive reads or optimizer starts. Do not restart it or reuse
its unused allowance.

[Every range and noise case](README.md) · [Frozen method](PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
