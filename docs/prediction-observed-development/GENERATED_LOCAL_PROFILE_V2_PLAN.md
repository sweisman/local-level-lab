# Corrected local-profile replay

The first radius-0.1 study was prepared but **never launched**. A source
review found that its final receipt comparison inherited an error: it
expected 119 new future receiver samples, although the evaluator reads the
119 sealed source positions. No native call or start was charged in that
prepared study.

This new study keeps the [same fixed local question and radius](GENERATED_LOCAL_PROFILE_PLAN.md).
It first verifies the sealed three-candidate forecasts and saves them before
opening later positions. It profiles all 26 calibration columns within ±0.1
normalized units and the original physical bounds, evaluates each corrected
native path, and records tangent remainder. It explicitly expects the
source construction charge minus the 119 samples read from the closed study;
all other construction and native charges must match exactly. One task,
one worker/thread, no new fit starts, one-hour wall cap and finite native
limits. Source, environment and recovery checks precede launch.

The prior full-range v1/v2 terminal failures remain unchanged. This is
development-only future-data compatibility, not earlier-only prediction or
a calibrated Earth-model decision. No observed or protected flight is read.
