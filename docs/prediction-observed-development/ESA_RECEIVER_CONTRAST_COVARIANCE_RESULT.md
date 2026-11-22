# Separate receiver errors help predict the GPS differences

A covariance model with separate terms for the three GPS solutions
predicted their differences well enough to advance to another development
test. It learned from six windows at a time and scored two omitted windows
from the same ESA flight. The calculation used only the differences
between GPS solutions.

| Error model for the two paired differences | Summed negative log score |
| --- | ---: |
| Same variance for every direction | −23,605.55 |
| Unrestricted covariance | −27,493.08 |
| Separate receiver covariances | **−27,563.91** |

Lower scores are better. The separate-receiver model improves the
unrestricted score by 70.83 units overall and does better in two of the
four folds. The largest improvement comes from the pair containing the
previously high-error steady window. In the slowest frequency band,
the unconstrained estimate for `pwrpak7` has two negative eigenvalues in
every donor fit. The calculation clips those values to zero as planned.
That behavior shows where the separate-receiver assumption strains the data.

The comparison cannot measure errors common to all three GPS solutions.
The receivers share an antenna, and the windows come from one flight.
The result keeps this receiver term eligible for testing in the forecast
covariance. It does not qualify the forecast covariance or open the seven
reserved flight groups.

All four tasks and three software checks passed, with 80 charged calls
and zero new aircraft fits.

[Frozen plan](ESA_RECEIVER_CONTRAST_COVARIANCE_PLAN.md) ·
[Verified evidence](esa-receiver-contrast-covariance-evidence/README.md)
