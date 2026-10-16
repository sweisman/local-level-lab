# Qualifying a two-sided boundary stopping check

The [saved audit](../ilvis0-stopping-audit-20261016/INTERPRETATION.md) found packet-boundary
clustering in all eleven unfinished primary fits across the six unresolved stretches.
Independent mathematical controls showed that the previous smooth stopping probe
can reject a genuine cusp minimum. No archival result is relabeled by that finding.

This candidate changes the formulation of the stopping probe at a known interior
timing knot. It retains the existing 1e−4 stationarity, 1e−8 relative objective,
1 mm per-axis RMS and 1 cm maximum position tolerances. Physical parameter bounds
remain unchanged. This is a new numerical policy, not deployment of the old rule.

The proposed check:

1. Require a finite feasible point exactly at a supplied timing knot and a complete,
   ordered local partition with physical endpoints −1 and +1. Never snap a nearby
   fitted point into acceptance. A later archive adapter must verify this geometry.
2. Evaluate the center twice, then both sides at two small scales. Verify repeated
   and extrapolated center values against the original cost and position tolerances.
3. Test stationarity in each side's feasible direction. On the left, a timing
   gradient pointing toward the right is constrained by the knot, and conversely
   on the right. Every nuisance coordinate retains its physical bounds and tests.
4. For each side, solve the undamped bounded affine correction over that whole
   adjacent interval and all nuisance directions. Evaluate the proposed correction
   with the full callback, checking actual objective and physical-position stability.
   A proposal reaching another unchecked interior knot must abstain.
5. Recheck feasible-side stationarity freshly, using a fresh side sample when the
   correction remains at the knot. Require both sides to pass. Preserve failures,
   finite call accounting and scientific abstention.

At most **ten callback evaluations and two affine solves per check**. The callback
contract requires qualified residuals and Jacobians; these software controls do
not validate the archival derivative adapter. All evaluations must be charged by
that future adapter. Only an exact single-knot interface is qualified here; the
nanosecond-separated cluster of receiver/packet knots needs separate handling.

Known-answer controls cover cusp minima and maxima, smooth minima/nonminima,
coupled unfinished nuisance fits, constrained nuisance optima, redundant directions,
shifted knots, discontinuities, repeatability, invalid geometry and finite budgets.
The sealed batch fixes **43 tests**, source/environment hashes, a maximum of
**688 analytic callback evaluations and 87 affine solves**, including the old-gate
comparison control. Run one qualification batch. Use four
threads and a ten-minute timeout; no retries, archive reads, native predictions or
observed fits. Completed batches cannot restart.

Passing this qualification establishes software behavior only. An archival adapter,
native checks and a separately frozen matched study are still required before a
new result can satisfy this policy. All existing labels and evidence stay unchanged.
