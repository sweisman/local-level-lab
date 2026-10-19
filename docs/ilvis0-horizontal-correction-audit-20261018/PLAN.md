# Saved horizontal correction audit

## Question

The completed full-calibration horizontal qualification passed eight of twelve
generated fits and three of six paired-start comparisons. Four flat-model fits
passed endpoint stationarity but failed fresh local stability. One zero-field
globe pair missed objective repeatability. Preserve every original outcome.

Inspect all twelve saved residual/Jacobian systems, not just failures. Reproduce
the existing bounded linear probe and compare two diagnostic formulations:
column scaling of the same feasible problem, and a column-scaled ridge penalty
of 1e-6 on normalized parameter displacement. The ridge formulation is a
different diagnostic objective, not a qualified replacement or a new gate.

Retain all 26/27 columns and physical step bounds. Report endpoint rank,
stationarity, predicted versus saved actual probe changes, correction sizes,
largest parameter moves and affine-solve completion. Compare the affine cost
with the feasible zero step independently of the solver's success flag.
An SVD reports rank only; it does not remove columns from any solve.

## Finite scope

- Twelve immutable endpoints; three bounded affine solves each: **36 solves**.
- Twelve diagnostic SVDs; four total numerical threads; sixty seconds.
- Zero native predictions, nonlinear optimizer starts, original-recording reads
  or scientific label changes. No retries, expansion or completed-run resume.
- Check parent manifest/completion/summary and published receipt hashes. Freeze
  input/source/environment hashes before numerical imports, journal each
  endpoint before work, save atomic results and an exclusive lock.
- Tests use constructed arrays only. Report rendering reads saved outputs and
  performs no linear solves. A later native probe needs a separate finite freeze.

The parent report inherited an incorrect display ceiling of 3,888 calls; its
frozen allowance was **1,944**, of which **1,294** were used. Preserve the parent
report and correct this presentation explicitly here. These software controls
do not alter the archive's 53 globe / zero flat / zero unresolved finding.
