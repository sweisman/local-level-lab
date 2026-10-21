# Saved bounds complete the calculation, but two cases remain too wide

**All 40 scheduled calculations passed. Four of the six model/processing cases
meet the original prediction-width target.** The two globe cases with the
specified background field still miss the east-coordinate target. This is a
limitation of the prediction-error calculation, not a new aircraft result.

The comparison took 139.46 seconds. It reused 280 saved bounds, with no new
integration, compiler invocation, optimizer start or aircraft-data read.

| Candidate / processing | North width | East width | Height width | Target |
|---|---:|---:|---:|---|
| Globe with specified field / zero removal | 1.0001 m | 1.4546 m | 0.7722 m | East fails |
| Globe with specified field / profiled removal | 1.0600 m | 1.4798 m | 0.8008 m | East fails |
| Globe with zero field / zero removal | 0.7666 m | 0.7998 m | 0.5658 m | Pass |
| Globe with zero field / profiled removal | 1.0659 m | 1.1220 m | 0.8799 m | Pass, inherited cover only |
| Flat disc / zero removal | 0.6459 m | 0.2002 m | 0.3924 m | Pass |
| Flat disc / profiled removal | 0.7440 m | 0.2370 m | 0.4865 m | Pass |

Each target is half that case's original width, fixed before these comparisons.
The two failed east targets are 1.4066 m and 1.4443 m: the new ranges are about
3.4% and 2.5% too wide. North and height pass in both cases. These are full
interval widths, not measured residuals, confidence intervals or sensor accuracy.

## What this adds

Earlier studies timed out before finishing some future bounds. Compatible
completed bounds can still be used without relabeling those failed studies.
The new comparison verifies their hashes, environments, sources, domains and
shared coefficients, then rebuilds and checks the training and future bounds.

Five cases have all eight newly calculated regions. The zero-field globe with
profiled removal lacks saved future bounds in two regions, so its entire result
uses the unchanged earlier complete cover. No favorable partial new union is
used. All six final ranges have complete coverage, but complete coverage alone
does not pass the width target.

## What remains

The next diagnosis must distinguish loose east-coordinate bounds from runtime
cost. Reusing certificates solved the incomplete-coverage obstacle; it did not
make both specified-field ranges narrow enough. Preserve this completed study
and its failed width outcome. Any revised calculation needs a separate finite
freeze, unchanged physical domains and the same acceptance target.

Even a successful short-example width test would leave recording-scale bounds,
floating-execution assumptions and the observation-error model to qualify.
The 53 aircraft model comparisons remain unchanged. No withheld-flight fit or
calibrated detection follows from this generated 7.2-second example.

[Verified calculation and accounting](README.md) · [Frozen scope](PLAN.md) ·
[Next steps](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
