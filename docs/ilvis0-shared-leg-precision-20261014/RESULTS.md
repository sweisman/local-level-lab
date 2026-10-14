# What the precision comparison found

All six fixed endpoints completed, using **84 integration evaluations and zero
archived-data optimizer starts**. All eleven arithmetic/derivative controls and
all six subsequent exact-motion solver controls passed.

Wider internal arithmetic improves the stringent stopping checks without changing
the physical equations, calibration bounds, observations or packet-clock convention:

- The two unfinished background-field fits pass their original full probe checks
  with wider arithmetic. Their cost-change ratios fall from approximately 1.06
  and 4.01 times the limit to 0.0095 and 0.0615 times the limit.
- One previously completed neighboring endpoint also passes the newer full probe
  check under wider arithmetic, after failing that check under ordinary arithmetic.
- The September disc endpoint remains outside the vertical stability limit:
  its full correction moves vertical predictions about 3.77 mm RMS, versus a
  1 mm numerical tolerance. More arithmetic precision does not resolve that case.

Overall, **five of six full probes pass under wider arithmetic**, compared with
two under ordinary arithmetic. Corrections recalculated from the wider derivatives
also pass at the same five endpoints. This identifies arithmetic precision as a
contributor to the cost-only stopping failures; it is not a new instrument correction.

These are fixed-point diagnostics, so the published findings remain **30 globe
preferences, zero flat and 23 unresolved**. A failed primary cannot be promoted
without its complete comparison and repeated-start qualification. The
[paired trial](../ilvis0-paired-precision-trial-20261014/README.md) tests that next.

[Full precision report and individual probes](README.md) and
[exact-motion solver controls](SOLVER_CONTROLS.md) retain the evidence and its scope.
