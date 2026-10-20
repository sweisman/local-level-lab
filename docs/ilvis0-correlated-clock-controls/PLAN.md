# Finite common-clock qualification

Qualify the exact rational prefix-clock component described in the
[method plan](../ilvis0-clock-correlation/PLAN.md). Freeze 24 generated identities:
eight exact dyadic clocks, eight fixed periods whose accumulated floating tags
round, and eight variable-period clocks. Each uses 16, 64, 128 or 400 packets.
Include interior, initial, final and prefix-boundary-crossing query intervals,
and a declared upstream time-map remainder in half the cases.

Check the first, middle and final prefix against an independent exact sum of
clipped durations. Evaluate every relevant packet start/end knot, interval
endpoints, center and seventeen fixed interior points. Verify selected one-sided
slopes, exact center/endpoint values and remainder containment. Exact dyadic
interior cases must retain only the supplied upstream remainder; rounded-tag
interior cases must satisfy the independently calculated clock-defect bound.
Unit checks also reject invalid tags, unsupported timing and exhausted resources
without advancing the state.

Limits: **24 identities**, at most 400 prefix appends and 1,000 oracle points
per identity: **9,600 appends, 24,000 oracle points and 9,600,000 primitive oracle
terms** overall. Reserve each full identity before calculation. Rational fields
are limited to 8,192 bits; core appends have five cooperative seconds per
identity, the full identity ten seconds, and the study 120 seconds. One worker
reserves four numerical threads; no native calls, observed fits, original-file
reads or ESA evaluations. No retries, extensions or process signals.

Every oracle value must be inside the bound and every exact first-order error
inside its remainder. Passing qualifies the mathematical clipped-period map,
not whole-program roundoff or the physical instrument clock. It permits only
preparing a separately frozen regrouped-native control. All Earth-model physics,
calibration bounds and completed evidence remain unchanged.
