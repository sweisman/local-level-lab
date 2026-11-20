# Derive calibration certificates for the surviving child ranges

The [first subdivision](ESA_LINKED_SPLIT_RESULT.md) excluded three children
using the directions inherited from their parents. The bound for either
candidate stayed unchanged. Use the same 15 surviving children from that
subdivision. Preserve all other boxes and their existing dispositions.

For each child, propose one earlier-loss direction by minimizing its
approximate earlier residual norm. Propose one forecast score direction by
maximizing the same archived signed contrast subject to the original
earlier loss and static constraints. Use the existing proposal solvers and
cap each search at 120 iterations. Certify both proposals against the
linked static map using outward arithmetic. The approximate solver can
propose a direction, but only the certificate can exclude a child or
lower its bound. Retain the best verified previous bound when the new
certificate is weaker. Recheck every saved feasible witness over the
unchanged cover. Recombine against the original 25.41-unit gap.

Use 15 identities with at most 60 charged calculations, two workers with
one numerical thread each, and a 120-second cooperative limit. Use zero
new trajectory fits, native integration, later GPS reads or reserved-flight
reads. Keep the original earlier-loss increase of 0.01, zero unshared error
and static-map allowances. Report any incomplete or invalid certificates
and preserve the unchanged bounds they leave in force. The full dynamic
remainder remains a separate requirement.
