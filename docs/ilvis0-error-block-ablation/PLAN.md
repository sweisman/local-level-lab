# Identify which internal error terms keep the ranges wide

The column-specific orientation comparison passes correctness but still misses
the fixed target. Do not repeat it or add another matrix-constraint grid before
locating the remaining width. Use a separate saved-only diagnostic.

Select the unique known-truth sector of each of the six existing generated
model/processing cases, after all source predictions are sealed. For each case,
temporarily fix exactly one existing auxiliary block to its stored known physical
value, leaving all other coordinates at the saved bounds:

| Block | Coordinates | Meaning |
|---|---|---|
| Reference terms | 27–32 | Shared velocity/clock and initial lever corrections |
| Acceleration/clock | 33–38 | Shared quadratic and linear clock effects |
| Acceleration remainder | 39–41 | Shared nonlinear acceleration approximation error |
| Force matrix | 42–50 | Shared nonlinear rotation/gain matrix error |

These are internal approximation allowances, not measured device noise. Supplying
their exact simulated values is an oracle-assisted ablation, unavailable for an
unknown real calibration. It cannot clear a prediction gate or be promoted as an
uncertainty method, even if its conditional widths meet the old target.

Local tests must check block indexing, preservation of all 51 coordinates,
rejection of an out-of-box anchor, an exactly known width reduction and an
unrelated fixed block that correctly leaves the width unchanged. Reuse the
qualified saved-support calculation and independent endpoint audit. Retain
all original training constraints and previous valid certificates as fallbacks.
Do not recompute native tangents, nonlinear bounds or source-reference maps.

Freeze 24 identities: six groups crossed with four fixed blocks. Allow six LP
proposals per identity, 144 total, and 576 exact support evaluations including
fallback and independent checks. Four workers use one thread each, with a
300-second cooperative allowance. Zero native calls, bounds, original aircraft
reads, observed fits or protected outcomes. No retries or budget expansion.

Verify each saved physical anchor against the source region before fixing any
block. Save the conditional ranges, bounds, certificates and explicit oracle
label. Check containment of the saved known future outcome afterward. Report all
24 outcomes, absolute widths and ratios to their unchanged source-sector widths.
The diagnostic uses one sector per case and does not replace the complete union
across all sectors. It does not assign additive percentages of total uncertainty.

Use the result to choose a stronger source-bound dependency or propagation
calculation. Preserve uninformative or failed outcomes without replacements.
Actual recording-scale usefulness, numerical treatment and observational error
coverage remain open requirements.
