# Value-only and tangent calculations agree at four aircraft points

Both calculations produced exactly the same coordinates, residuals and
packet-boundary counts at all four saved points. The tangent calculation also
reproduced the saved fitted residuals and the cost of the fresh correction.

| Recorder and model | Saved point | Tangent CPU | Value-only CPU | Speed ratio |
|---|---|---:|---:|---:|
| IMU8, zero-field disc | Endpoint | 52.02 s | 0.45 s | 116× |
| IMU8, zero-field disc | Fresh correction | 36.70 s | 0.76 s | 49× |
| IMU8, specified-field globe | Endpoint | 52.62 s | 0.74 s | 71× |
| IMU21, specified-field disc | Endpoint | 38.70 s | 0.79 s | 49× |

Timing uses process CPU time, excluding compilation and artifact writes.
These are individual evaluations. The existing solver also needs derivatives
for accepted steps and its final stopping probe. A matched full-fit study
must verify that checking proposed steps with the faster calculation preserves
the solver path, stopping results and forecasts at equal iteration limits.

The [frozen check](MATCHED_TRIAL_PROBE_PLAN.md) completed all three tasks and
charged exactly eight native calls. It started zero fits and used no later
receiver positions. The original zero-field disc stopping failure remains in
the record. See the [sealed evidence](../ilvis0-matched-trial-probe-runtime/README.md)
for the paired arrays, timing observations, source and accounting.
