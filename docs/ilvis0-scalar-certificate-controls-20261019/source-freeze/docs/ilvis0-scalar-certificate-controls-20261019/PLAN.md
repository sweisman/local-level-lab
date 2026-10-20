# Scalar calibration with an algebraic feasibility check

## Purpose and preserved evidence

The preceding nonlinear study completed all 228 identities but qualified only
32/72 comparisons. Many unfinished endpoints had almost-zero residuals in flat
calibration directions. Preserve those failures; this is a separate candidate,
not a restart or an expansion of its allowance.

Before optimizing, test a simple feasible construction. Let m be the measured
body-force magnitude history and q the candidate's required-force magnitude.
Compute one constant isotropic gain g=(qᵀm)/(qᵀq)−1, with zero offsets and zero
gravity adjustment. Reject this construction if g exceeds any axis gain bound.
Do not clip it. It is a sufficient construction, not an exhaustive search.

Recompute residuals and the complete seven-column Jacobian at that point.
Accept an algebraic near-zero certificate only when physical RMS is at most
10⁻¹² m/s², maximum absolute residual at most 10⁻¹¹ m/s² and fresh projected
stationarity at most 10⁻⁸. Publish the feasible objective and its nonnegative
lower bound of zero, not an assertion of a unique calibration or exact global
optimum. Repeated starts reaching the same algebraic construction are identified
as certificates, not independent optimizer convergence.

Otherwise run the original bounded nonlinear candidate with the original
requested start and 200-evaluation limit. Preserve its analytic derivatives,
seven bounds, numerical tolerances and fresh endpoint gate unchanged. There is
no retry or automatic replacement of an unsuccessful result.

## Fixed qualification and matrix

Use the same four independent planted fixtures and three starts as the prior
study: twelve known-answer identities, followed only after their qualification
by the same 72 sealed constructed histories with three starts each. No new
trajectory is chosen to improve the result.

Qualification still requires all twelve endpoints, RMS ≤10⁻⁷ m/s² and residual
history agreement ≤10⁻⁷ m/s². Matrix acceptance still requires all three endpoints,
RMS-score spread ≤10⁻⁸ m/s² and residual-history spread ≤10⁻⁷ m/s². No wrong-model
separation is required. Report certificate use separately from actual optimization.

## Finite frozen allowance

- 228 charged identities, with at most 228 mathematical optimizer starts.
- At most 404 residual/Jacobian calls per identity: two feasibility calls plus
  the original optimizer/fresh-check ceiling of 402. Accepted certificates use
  two initial and two fresh calls, without running an optimizer.
- At most 92,112 residual/Jacobian calls overall, plus two explicit magnitude
  history constructions per identity. No original-file reads, observed starts
  or native integrations. No retries.
- One worker, four total numerical threads, 300-second wall-time ceiling.
- Seal source, environment, input and policy hashes before launch; charge before
  execution. Qualification failure blocks the matrix. Completed work cannot resume.

The analytic branch cannot declare a different physical model correct. It can
only exhibit one allowed calibration matching a scalar necessary constraint.
It supplies neither a complete gyro-free motion history nor statistical coverage.
Recorded-data use still needs C03's timing, averaging, calibration and uncertainty
qualification. The main 53-stretch results and all earlier failures remain intact.
