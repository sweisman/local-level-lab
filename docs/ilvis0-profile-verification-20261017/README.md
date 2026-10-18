# Check the saved timing solutions

The two fixed time offsets were fitted from both saved starting solutions. All
four fits reached their conditional stopping checks, but a final diagnostic was
blocked by a call-accounting error. This follow-up checks their saved endpoints
with twelve fresh native evaluations at most and no refitting.

It tests whether the same fixed time gives the same nuisance fit, and preserves
the derivative with respect to time. Fixed-time agreement does not establish a
fully converged free-time fit or change the public model comparison.

The verification is complete: all four endpoints passed, using all twelve native
calls. At each fixed time, both starting solutions agree within the existing
cost and track-repeat limits. The two different time offsets still give distinct
costs, so the full free-time comparison remains unresolved.

[Results](RESULTS.md) ·
[Finite plan](PLAN.md) · [Original profile trial](../ilvis0-fixed-time-profile-20261017/README.md) ·
[Current findings](../CURRENT_STATUS.md).
