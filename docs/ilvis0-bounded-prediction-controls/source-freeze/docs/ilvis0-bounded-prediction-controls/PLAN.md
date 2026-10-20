# Training-only bounded predictive uncertainty

## Gap to address

The earlier matched prediction study completed 10/12 fits. Its error predictions
conditioned on fitted calibration, while local geometry and finite axis probes
did not establish bounded nonlinear or covariance-estimation uncertainty. The
new supplied-covariance operations remove a memory obstacle, not this gap.

The next software candidate must preserve the following distinctions:

- One shared error family and scale assessment for all physical candidates;
  never inflate a candidate's own residual-derived scale to rescue its fit.
- Training/calibration observations determine nuisance/error assumptions.
  Prediction observations cannot enter scale selection, initialization or corrections.
- Bounded nuisance directions remain present even if training data cannot identify
  them. A singular value cutoff must not silently erase their prediction effect.
- Global nonlinear-remainder allowances are explicit assumptions to qualify.
  Saved axis-probe discrepancies are not global bounds over a parameter box.

## Proposed qualification sequence

1. Add structured conditional prediction from training innovations state. Match
   dense conditional means, variances and covariance-response norms on small
   problems; accept future epochs/design/transforms, never future observations.
   Preserve drift's full-record origin/span and state continuity.
2. Qualify a training-only shared scale bound and finite covariance-family
   sensitivity. A calibration source/reference mean must be frozen once for all
   candidates. A union over admissible covariance alternatives retains uncertainty;
   picking a separate covariance/scale for each model is not the same procedure.
3. Construct bounded linear-mean confidence regions, including deterministic
   approximation error. Keep the parameter box and all original columns.
   Unidentified components receive box-based prediction ranges, not zero variance.
4. Combine parameter ranges, conditional future error and declared model remainder.
   Check exact known answers, active bounds, rank loss, scale uncertainty,
   correlated errors and deliberately inadequate models. Report unsupported or
   empty regions rather than forcing an interval.
5. Only after those controls, qualify the native adapter's training dependencies
   and nonlinear-remainder treatment in a separately frozen finite scope. Then
   prepare the representative retrospective NASA blocked-prediction study.

## Mathematical design to verify

For a supplied covariance alternative, whiten the training observations and
mean design. Allow an explicitly bounded whitened nonlinear remainder. A fixed
training/calibration reference design with positive residual degrees of freedom
can produce an upper noise-scale bound using a lower chi-square quantile;
deterministic remainder enlarges the residual norm before forming that bound.
This shared scale assessment must not be recomputed separately for Earth candidates.

The calibration reference design must be fixed before its calibration errors
are observed; a data-dependent reference cannot use the residual chi-square
shortcut. A candidate Jacobian learned from its own training data instead uses
the full training-noise dimension for its norm bound. A rank-degree bound is
reserved for an independently fixed design.

With that scale bound, a projected training-noise radius plus the declared
remainder bounds the identifiable mean component. Preserve the full parameter
box for its null directions. Linear prediction supports can conservatively
combine the identifiable ellipsoid with null-direction box supports, intersected
with the full-box support. This avoids treating a local unconstrained covariance
as the complete nuisance uncertainty.

If numerical rank truncation is used, account for the discarded design response
over the entire parameter box as additional approximation error. No parameter
column is dropped from prediction. Zero residual degrees of freedom or an
unsupported remainder prevents a calibrated scale claim.

For a Gaussian supplied error family, conditional future noise has a known
covariance. Simultaneous Gaussian marginal bounds with Bonferroni accounting,
multiplied by the shared scale bound, supply a conservative future envelope
without requiring independent coordinates. The training-remainder effect
on the conditional mean must also be propagated, not just future mean error.
Allocate the total error allowance explicitly among scale, nuisance and future-
noise events; independence is not needed for a union-bound guarantee.

Any coverage result applies only under its stated Gaussian family and supported
global remainder assumptions. A finite covariance union covers that family,
not arbitrary unmodeled temporal dependence. Physical adequacy and independent
confirmation remain separate empirical requirements.

## Execution boundaries

Start with small deterministic/software controls and separately frozen finite
coverage/scaling checks. Do not rerun completed studies, trigger native archive
predictions during preparation, consume ESA confirmation groups or promote a
production threshold. Existing observations, primary findings and failure labels
remain unchanged. Native fits require their own finite identity/evaluation freeze.

[Structured covariance](../ilvis0-structured-error-controls/INTERPRETATION.md) ·
[Earlier prediction results](../ilvis0-prediction-covariance-20261012/RESULTS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
