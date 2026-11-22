# Test a motion-dependent scale for forecast innovations

Use the eight original matched turn and steady windows from the
[variance-range check](ESA_COMPONENT_SCALE_FEASIBILITY_RESULT.md).
Retain both inertial error descriptions, the fixed forecast means and
the original steady and maneuver covariance components. Only the native
covariance changes. Score all 120 later receiver reports in each window.

Let `L` be the native factor. Scale its chronologically ordered
innovations by `q + d*w(t)`, the same for the three coordinates of a
report. Start the weight at zero. At each report it approaches the indicator
of positive archived angular exposure with an exponential time constant
of 15 seconds, the existing maneuver response time. It uses only
exposure available by that report. The resulting native covariance is
`L * diag(q + d*w) * Lᵀ`, plus the unchanged added terms.

Compare the original covariance, a fitted constant `q` with `d=0`,
and fitted `q,d`. In each fold use exactly the other three pairs to
score the grid. Use natural logs −5 through 5 in integer steps for
both positive coefficients. Minimize the joint Gaussian negative log
score with deterministic ties favoring the smaller coefficients. Only
after selecting scales, read the two scoring windows. Compare joint
negative log scores and the original descriptive error reference.
The matched windows share one flight and reuse development data. This
cannot qualify independent-flight coverage.

Use a whitened diagonal-plus-root likelihood with the unchanged added
components. Verify it against a dense covariance, including a generated
case where matched motion is informative. Also test causality, quiet
motion, boundary handling and the withheld-window split. Bind the
archived factors and angles before numerical work. Freeze eight tasks,
one thread, 120 seconds and 798 candidate window likelihoods per fold.
Allow two fixed-score verification calculations per window. No forecast
is repeated and no reserved flight is opened.
