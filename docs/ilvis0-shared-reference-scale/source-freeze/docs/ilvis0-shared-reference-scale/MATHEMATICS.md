# A shared noise-scale bound without a fitted Earth candidate

The prediction method needs one error assessment shared by all physical
candidates. A candidate must not assign itself larger measurement uncertainty
because it fits badly. This alternative uses a fixed training-only reference,
and permits that reference's mean trajectory to be wrong.

Let the whitened training observations be `z = mu + sigma*epsilon`, where
`epsilon` is standard Gaussian and `mu` is any deterministic mean. Let `P` be a
fixed orthogonal projection with positive rank `d`, chosen independently of
these observation errors. Then

\[
\|Pz\|^2/\sigma^2\sim\chi^2_d(\lambda),\qquad
\lambda=\|P\mu\|^2/\sigma^2.
\]

The noncentral distribution is a mixture of central chi-squares with `d+2K`
degrees of freedom, where `K` is Poisson with mean `lambda/2`. Each additional
pair of degrees adds an independent nonnegative chi-square term. Consequently
its lower-tail probability at any threshold is no greater than the central
`d`-degree lower tail. For the central lower quantile `q_alpha`,

\[
\Pr\!\left[\sigma>\frac{\|Pz\|}{\sqrt{q_\alpha}}\right]\leq\alpha.
\]

A supported deterministic numerical allowance for evaluating the residual norm
can be added to its numerator. No bound on the reference mean is needed for
this one-sided scale result. A poor reference can make the bound very wide;
it does not justify treating its residual as a precise noise estimate.

## Conditions and limits

The covariance shape and Gaussian error law are assumptions, not conclusions
of this calculation. The projection must be fixed independently of the same
errors. A fixed time-polynomial design is eligible in principle; a Jacobian
learned by fitting these positions is not. Projection rank can be chosen from
the fixed design, but must leave positive residual degrees of freedom.

All physical candidates use the same scale source and covariance-family member.
No withheld positions enter its construction. Unknown arithmetic allowance,
unsupported distribution, adaptive reference or zero residual dimension means
no bound. This does not assess covariance-shape adequacy, non-Gaussian errors,
selection effects, physical-model adequacy or a calibrated detection threshold.

The earlier bounded-mean method and its frozen evidence remain unchanged. This
is a separately identified alternative for the roadmap's shared error assessment.
Generated controls and a finite freeze must qualify it before archive use.

[Prediction mathematics](../ilvis0-bounded-prediction-controls/MATHEMATICS.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
