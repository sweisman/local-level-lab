# How much carrier error could change the score?

Under the stated motion and anchor assumptions, changing the saved two-minute
ESA comparison by its full score gap requires **at least 1.97 mm RMS** of
structured carrier-range error. The earlier replay found that one particular
displacement would require 3.01 mm RMS. This calculation bounds all directions
of displacement in the linear range model, so the earlier example's larger
value should not serve as an error threshold.

The calculation uses 240 half-second pairs and 2,496 range values. It assumes
that the displacement vanishes at the four permanent Nuuk times and at both
endpoints. The 1.97 mm example also assumes that the displacement's RMS
acceleration is at most 1.876 mm/s², taken from the earlier constructed example.
Neither the exact positions nor the acceleration cap is an observed accuracy
limit. The result gives a target for an independent error measurement.

For a carrier-range error of RMS magnitude \(R\) in metres and a displacement
acceleration of RMS magnitude \(A\) in m/s², the reported upper bound on the
score change is approximately \(22.8216R + 0.0004464A\). The saved score gap
is 0.0449584. The first term uses the norm of the saved carrier weights. The
second accounts for score times between carrier samples and for any unresolved
score weights after the numerical solve. Most of that second term comes from
the small differences between the score and carrier timestamps.

This is a sensitivity bound for fixed satellite geometry and linearized ranges.
The in-sample carrier residual includes the effect of fitting the saved path,
so it does not supply the independent error cap needed to use the bound as a
decision. The reserved ESA flights remain unopened.

Ten software tests passed. The [frozen plan](ESA_CARRIER_SCORE_BOUND_PLAN.md)
closed at 242 of 242 charged checks, with zero new fits and zero reserved-flight
reads. The [signed certificate](esa-carrier-score-bound-result.json) has SHA-256
`12c0f807d4e710cf05fc3dc521ad9e05f2ba69df8e53f95bcf47dd541b6295bb`.
