# Apply the checked remainder to complete-history prediction

## Question and design

The completed long-history test retained a 53.16 m/s² acceleration Taylor
remainder in its integration. A separate candidate subsequently passed all
twelve short native controls with a smaller, independently checked remainder.
Test that candidate on the same complete histories before developing another
bound or repeating the whole training calculation.

Reuse the six generated 96,000-packet cases, final 30-row training regions,
conditioning certificates, calibration references, source bounds and native
value/Jacobian results from the completed full-history study. Verify every
parent completion/result/input/artifact hash. Keep all 27 physical directions,
24 shared error coordinates, original broad limits and ±1-second clock range.
No aircraft measurements or reserved ESA outcomes are used.

Only recompute the bound at 438 seconds, using `lll.ilvis0_remainder_native` and
its checked bridge. This integrates the complete history; it is not a short
prefix test. Retain the earlier training constraints without recomputing or
tightening them. Reuse the original centre and Jacobian; require the new bound's
centre to meet the already qualified 1-micrometre comparison tolerance.
Require unchanged source bindings, shared coefficients and normalization caps,
and nonwidening remainder arrays. The smaller operational Taylor remainder must
not replace the original shared-coordinate normalization.

Recompute future supports with the existing saved-prediction builder, retaining
old dual certificates as a safe fallback. Verify all six new supports and
outward endpoints independently with exact fractions. Save the new prediction
before opening the separate saved truth-audit input. Require retention of the
unchanged training witness and containment of the saved future truth.

Success still requires total width at most 20 m north, 20 m east and 50 m height
in every case. Wide ranges remain failures even if containment and software
checks pass. This endpoint does not qualify the whole prediction period or an
aircraft error law, and cannot authorize observed-data prediction fits by itself.

## Implementation and checks

1. Add a standard-library envelope verifier to the shared saved-prediction
   audit library. Check all 51 columns, coordinate scales, origins, source
   identities, signed certificates and exact endpoints. Known-answer tests
   must reject changed coefficients, missing columns and mismatched sources.
2. Add a small shared evaluator for the existing saved-conditioning workflow.
   Reuse the qualified remainder candidate, bridge, compiler loaders, support
   builder and indexed journal. Do not copy an integration engine or worker.
   Test charge-before-execution, input rejection, failure preservation and
   delayed truth access with cheap deterministic controls.
3. Verify the twelve completed short controls and six parent completions;
   freeze the complete source/input/environment/compiler dependencies, then
   launch the six fixed identities through `lll.studies`.
4. Publish every outcome and immutable charge record. Update the roadmap and
   study index, preserving all earlier prediction failures and model comparisons.

## Finite allowance

There are six identities and no retries. Each has one reference reconstruction,
one conditioning-proof reconstruction, two conditional-remainder certificate
calculations, one matched-bound comparison, one saved-truth audit, six LP
proposals and 30 exact support checks. Those support checks comprise six for
the saved conditioning proof, eighteen inside the proposal/fallback builder
and six independent future checks.

Each identity reserves one complete 96,000-packet bound: source, derivative,
point and direct streams and all 96,000 body bounds, with 864,000 logical bound
steps. Totals: six bounds, 5,184,000 logical steps, 36 LP proposals and 180 exact
support checks. There are zero native value/Jacobian queries, optimizer starts
or original aircraft reads. Reused outputs remain charged to their original
study and are not presented as new observations.

Use four workers, one numerical thread each, with no other numerical allocation.
Previous late bounds took 3,686–4,223 seconds each; expect about 2–2½ hours for
the six-case comparison, allowing for contention. The cooperative ceiling is
7,200 seconds per bound and 18,000 seconds overall. Never signal a process,
expand an allowance, retry a failure or discard a case to improve the outcome.

[Completed full-history test](../ilvis0-long-staged-feasibility-v2/README.md) ·
[Qualified short candidate](../ilvis0-remainder-native-controls/README.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md) ·
[Reproducibility](../REPRODUCIBILITY.md).
