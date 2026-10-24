# Does calculation precision explain the ESA stopping failures?

## Question

The completed stopping diagnostic reproduces every saved calculation exactly.
Seven field-globe fits still fail cost stability despite local position changes
below 4 micrometres. Test two possible numerical effects separately: rounding
when longitude differences are wrapped, and rounding accumulated during integration.
This is a diagnostic, not a revised fit or an excuse to accept failed fits.

## Fixed comparison

Use all 24 previously checked source identities. For each, reuse precisely the
saved fitted point and its saved bounded correction, without recomputing that
correction or selecting a new direction. Use the same earlier 800 positions,
training-support increments, initialization, covariance and height-gravity anchor.
No later observations, original aircraft files or protected flights are inputs.

Calculate each point in binary64 and extended precision. Reuse the binary64
output to compare the legacy longitude wrap with a wrap that leaves already
in-range differences untouched; do not charge or run an extra native sweep for
that algebraic comparison. Subtract receiver coordinates before converting
extended results to binary64. Preserve binary64 packet-clock accumulation,
query dispatch, query fractions, parameter products and processing-fraction
mapping. Derive the scalar equations from the exact hash-bound original C++
source; do not copy or revise the physical mechanization. Require genuinely
wider arithmetic on the host.

The three reported modes are binary64/legacy wrap, binary64/stable wrap and
extended/stable wrap. The binary64 legacy result must reproduce both saved
residual vectors exactly. Save a mismatch and stop that identity if it does not;
do not continue to obtain a more favorable result. Report costs, cost changes,
physical position changes and numerical provenance for every returned mode.

## Qualification and allowance

Before preparation, qualify exact source/layout rejection, preservation of small
longitude differences, a known-answer sub-binary64 coordinate displacement,
all three physical candidates and both processing cases, full calibration
vectors, fractional timing, height-dependent gravity, charge-before-execution,
reference-mismatch rejection and unchanged labels. Bind the passing test report
to source and environment hashes. Preserve the earlier precision implementation
and its historical controls unchanged.

Freeze **24 identities, 96 value sweeps, 18,421,785,600 packet/query work units**,
four workers with one numerical thread each, and a cooperative one-hour ceiling.
There are zero optimizer starts and retries. Charge each native call before
execution; save each returned array before judging reference agreement. No unused
allowance transfers from a completed run.

No mode changes an original convergence label, threshold or scientific decision.
An improvement would motivate separately qualified solver work. A negative result
is retained and redirects diagnosis. Seven confirmation groups remain protected.

[Completed stopping diagnostic](../esa-stopping-resolution/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
