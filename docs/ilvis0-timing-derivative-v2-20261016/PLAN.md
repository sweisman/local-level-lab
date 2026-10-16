# Corrected fixed-endpoint timing diagnostic

This separate freeze checks the two target endpoints left unevaluated by the
[previous diagnostic](../ilvis0-timing-derivative-20261016/RESULTS.md). Its completed
control is reused with hashes verified. No earlier allowance is reopened.

The earlier coupled BVLS correction added −2.220446049250313e−16 to an already
normalized −1 gyro-bias coordinate. The computed endpoint was −1.0000000000000002,
so strict preflight rejected both target identities before any native calls.
The original errors, charged identities and control remain preserved.

The correction applies only to construction of the diagnostic's coupled endpoint:
an overshoot of at most four machine epsilons at normalized ±1 is snapped to the
unchanged bound. Every adjustment records the parameter, computed value and
evaluated value. The corrected step is used for both actual and linearized
comparisons, including its half step. Nonfinite values, larger violations,
infeasible centers and infeasible time perturbations remain errors. Scientific
fit bounds, solver acceptance and instrument assumptions are unchanged.

Fixed scope:

- Primary and repeat of `fd7b81e48a4122b149c4925b`, using the same saved fitted
  endpoints, original BVLS correction, profiled-removal case and zero-field globe.
- **Two diagnostic identities / 24 native calls maximum**, twelve per endpoint,
  **zero optimizer starts**, no retries, one worker with four numerical threads.
- Two identical center predictions; symmetric time-offset shifts of 0.1 µs,
  10 µs, 1 ms and 4 ms; full and half coupled corrections. All other inputs
  and the numerical comparison methods match the preceding diagnostic.
- Verify the preceding complete control and both zero-native-call error records,
  original hashes, selected intervals, extraction provenance, source snapshots,
  numerical environment and central objective reproduction.
- Record calls before evaluation, retain interrupted/error identities without
  retry, write atomic hashed results and reject duplicate workers or completed
  restarts. Packaging performs no predictions.

Estimate: roughly 15 minutes at the control's measured call speed. Finite-difference
agreement, packet crossings and coupled objective changes are numerical diagnostic
results. No stretch is relabeled and no additional fitting allowance follows.
