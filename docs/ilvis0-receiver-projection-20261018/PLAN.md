# Fixed-parameter receiver-coordinate comparison

## Fixed population and question

Use exactly the **18 stretches and 108 primary fits** with complete saved
artifacts in the completed contribution inventory. Their selection depends only
on artifact availability and consistency, before computing coordinate-projection
results. Preserve the other 35 stretches as out of scope for this diagnostic;
their completed model comparisons remain unchanged.

At each saved full-fit parameter point, calculate the full-position, horizontal-only
and height-only receiver objective using each subset's correct marginal covariance.
Apply the same projection to the complete nuisance Jacobian. Report local singular
spectra and numerical rank while retaining all parameter columns. Do not optimize
parameters, decode recordings, integrate increments or update model dispositions.

## Finite allowance

| Operation | Maximum |
|---|---:|
| Charged stretch groups | **18**, once each |
| Saved primary linearization reads | 108 |
| Saved epoch reads | 108 |
| Shared covariance constructions | 18 |
| Batched formal 3 × 3 covariance eigenvalue checks | 18 batches, at most 668 blocks each |
| Dense Cholesky factorizations | **126** |
| Residual/Jacobian projections | **324** |
| Singular decompositions | **324** |
| Native predictions / optimizer starts / original-recording reads | **0 / 0 / 0** |
| Numerical allocation | **4 total threads**, one worker |
| Wall limit | **20 minutes** |
| Retries | **0** |

Each stretch uses three projection adapters with two factorizations each and one
additional full-covariance factorization for common physical error summaries.
The largest full covariance is 2,004 × 2,004. Expected runtime is a few minutes;
operation and wall limits remain fixed even if the estimate is wrong.

Software qualification is one 31-test batch, capped at 60 seconds: the 19
projection controls, eight group/comparison/rank controls and four worker/budget
checks. It uses constructed matrices and fixture metadata, with no original
recordings, native predictions or archive arrays. Seal the successful test result,
exact input artifacts, software/source snapshots, numerical versions, this plan
and the finite allowance before launch. An allowance mismatch blocks execution.

## Assumptions and checks

Reuse the original `h1_v3_tau60` receiver covariance with formal NEU standard
deviations 0.3, 0.3 and 0.7 metres. Covariance is shared by every model/case within
a stretch. Validate the exact saved parameters, residual cost and all columns
against the completed inventory. All six primaries must share the same receiver
positions and relative-time layout; a mismatch is a recorded failure, with no
substitution or interpolation.

Retain both processing assumptions and all three models. Compare the globe
family's smaller cost with the flat-disc cost separately for each projection
and processing case. The reported ranking is explicitly at the saved parameters.
The full projection must reproduce the existing objective; a marginal objective
cannot exceed that full objective beyond numerical roundoff.

Convert full residuals to common physical north/east/up error summaries for context.
Coordinate-constraint removal does not remove the same coordinate from selection,
initialization, covariance construction or propagation. Both actual IMU channels
remain in the fitted predictions. This is not an isolated gyroscope analysis,
an independently optimized ablation, a calibrated significance test or a new
background-field measurement. Numerical rank is descriptive and does not change
the scientific eligibility policy.

## Persistence and publication

Use an exclusive worker lock, atomic hashed group outputs and an append-only
start journal. A charged group or completed batch cannot restart. Preserve errors
and partial output; do not reuse any completed allowance or adapt the population.
Publish completion hashes, operation counts, software checks, source snapshots,
per-fit CSV and matched-comparison CSV. Packaging completed results performs no
matrix operations. Published findings stay **53 globe / 0 flat / 0 unresolved**.
