# Recovering the complete long-history comparison

This software check recovers reports lost when a Python tuple/list comparison rejected numerically identical JSON data. Earlier failure records remain unchanged.

| Candidate | Processing | Evidence | Result |
|---|---|---|---|
| Globe + field | Zero removal | New cached reports; saved original and point checks | Complete reports equal |
| Globe + field | Profiled removal | New cached reports; saved original and point checks | Complete reports equal |
| Stationary disc | Zero removal | Both cached reports retained previously | Complete reports equal |
| Stationary disc | Profiled removal | Both cached reports retained previously | Complete reports equal |
| Globe, zero field | Zero removal | New cached reports; saved original and point checks | Complete reports equal |
| Globe, zero field | Profiled removal | New cached reports; saved original and point checks | Complete reports equal |

**6/6 histories have complete verified comparisons.**

Each history has 96,000 generated IMU packets and queries at 290 and 438 seconds. Complete reports must match exactly, all 51 coefficient columns must agree, and the saved independent point checks retain their original arithmetic tolerance.

The recovery used 4 new two-query cached batches, zero new original calculations and zero new point-oracle calls. It changes no physical model, calibration bound, prediction target or scientific finding.

This qualifies long-history reuse only when all six comparisons pass. Whole-record prediction uncertainty and observational coverage remain separate gates.

[Frozen limits](PLAN.md) · [Original run and failures](../ilvis0-native-prefix-long-v2/README.md) · [Prediction gates](../ilvis0-joint-projection-controls/NEXT_PLAN.md)
