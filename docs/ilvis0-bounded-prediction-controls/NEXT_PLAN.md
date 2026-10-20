# From software coverage to aircraft predictions

The frozen generated-data qualification is complete. All eight checks pass;
the six 512-realization coverage controls each have an exact one-sided 99%
lower bound above 0.95. No archive measurements were used. These results qualify
the uncertainty calculation for its stated Gaussian family and bounded mean
errors, not those assumptions for actual aircraft observations.

## Native adapter qualification

1. Audit the existing native uncertainty adapter's dependencies. Training
   initialization, calibration, covariance assessment and Jacobians must never
   depend on withheld positions or fused navigation. Keep every calibration
   column, including unidentified and boundary directions.
2. Express native predicted positions, training design and future contrasts in
   the same declared receiver coordinates and covariance convention. Preserve
   covariance time origin/span and integration state at the split. Check these
   dependencies against independent known-answer controls before archive use.
3. Establish an explicit nonlinear approximation allowance over the complete
   parameter region used for prediction. Local axis probes or sampled extrema
   are diagnostics, not a global guarantee. An unsupported bound must produce
   an abstention rather than a narrow interval. Test deliberately inadequate
   mean models and near-boundary cases, alongside exact controls.
4. Freeze one shared calibration/error reference and a finite covariance family
   for all physical candidates. A candidate cannot estimate a more forgiving
   scale from its own poor residuals. Distinguish externally supplied assumptions
   from error properties assessed on training data.
5. Freeze representative retrospective NASA splits, adequacy criteria, input
   dependencies and a separate finite numerical allowance before evaluating
   withheld observations. Report horizontal and vertical prediction errors;
   no good horizontal score excuses an implausible height path.

The source, selection and original findings remain unchanged. The earlier
incomplete prediction trial remains historical development evidence. The
completed software study cannot restart or supply another study's allowance.

## Independent prerequisites

If a global native approximation bound or an observational error assumption
is unsupported, dependent prediction fits stay blocked. Software investigation
can continue, as can the roadmap's ESA eligibility and rate-adapter prerequisites.
Those use source integrity, timestamps and receiver trajectory, with no model
outcome inspection. Recording 187 remains development material; all other ESA
groups retain their confirmation reservation. No archive-wide fitting follows
automatically from this software result.

[Coverage results](README.md) · [Mathematics](MATHEMATICS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
