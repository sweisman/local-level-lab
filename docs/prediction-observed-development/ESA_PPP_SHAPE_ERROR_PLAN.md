# Measure receiver disagreement in the fixed shape score

Use the three original precise point positioning (PPP) receiver exports
from opened recording 187. Reuse the archived 400/120 timing, local
coordinate scale, matched-field shape direction and full working
covariance. The signed shape score for the original export is the
reference. For each alternate export, report how its matched positions
change that score on the same 520 reports. Report the raw time match and
the effect of the previously used first-order time correction separately.
An incomplete match gets no score. Do not fill any missing epochs.

Also apply the fixed score weights to the two exports' disagreement with
the original across the 195 previously identified fast windows. Use
120 one-second reports from the fixed window and the immediately
preceding 400 one-second reports when available. Require matches within
2 ms and keep the outcome for every window. Exclude any window whose
520-report support overlaps the 400/120 model comparison. Record those
exclusions in the ledger. These translated weights probe the time pattern
of receiver disagreement on one flight. They do not measure the shape
separation on the other windows or establish between-flight coverage.

The calculation is limited to one pass over the three previously verified
receiver exports, one archived covariance restoration and one adjoint
calculation. Use the original per-export hashes and match counts. No
integration, fits or protected group reads are allowed. The receiver
paths share an antenna, so common receiver errors remain outside this test.
