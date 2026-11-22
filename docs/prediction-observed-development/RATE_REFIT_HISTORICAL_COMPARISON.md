# Why the newer ESA fit differs from the earlier accurate fit

The same 20-minute ESA development recording has two different training-only
results. The later errors below score saved, uncorrected IMU trajectories;
the weighted model's forecast conditioned on earlier receiver errors was not
calculated. This comparison uses the sealed results; it performs no new fit and
does not inspect any of the seven reserved confirmation groups.

| Calculation | Training horizontal error | Later horizontal error | Fit evaluations |
|---|---:|---:|---:|
| Earlier wide-precision pilot, short-memory receiver errors, start 0 | 0.057 m | 7.803 m | 25 |
| Newer rate-refit study, original linear-point increments, increment error law, start 0 | 39.961 m | 249.411 m | 9 |

Both fits converged under their own stated stopping checks. The older fit
passed its preset physical-accuracy screen; the newer fit failed the same
10 m horizontal RMS screen in both sections. Neither result is a calibrated
Earth-model detection.

The two studies have identical SHA-256 hashes for the prepared IMU interval
(`41c03b17…784`) and the 800 training receiver rows (`d37af49e…7d1`).
Their saved training records also match exactly on the 239,867-packet prefix,
all three prefix-array hashes, receiver-weight configuration
(`685890a2…6b77`), and GPS time origin. Both use the specified-field globe,
no upstream removal, packet-header elapsed time, the same 26 calibration
parameters and bounds, and start 0. The older calculation already used the
short-memory receiver policy, so a changed receiver policy does not explain
the difference. The newer study reproduced its own saved linear-point fit and
forecast exactly; the comparison here is with a *different, earlier* fit.

The main intended modeling change is the treatment of IMU error. The earlier
training objective weights receiver-position errors alone. The newer objective
adds a declared, temporally correlated IMU-error process to the observation
covariance. Its noise levels came from generated development controls, not
from a measurement of this physical instrument. The fitted parameters move:
for example, normalized Z gyro bias changes from −0.178 to +0.141. Neither
new fit is pinned to a calibration bound. The old and new source freezes also
contain support changes for structured whitening and native residual storage;
the native wide tangent source hash is identical. This saved comparison cannot
assign the entire accuracy loss to one source change or establish which
covariance is physically correct.

That [matched, training-only weighting control](WEIGHTING_CONTROL_RESULT.md)
has now completed. The current code, with receiver-only weighting, reproduces
the earlier parameters and forecasts exactly: 7.803 m later horizontal RMS.
Adding the declared IMU-error covariance in the matched current-code fit gives
249.411 m for the uncorrected trajectory. The added law is therefore the
operative difference on this recording; its physical validity remains
unestablished. A [later fixed-parameter check](CONDITIONAL_FORECAST_RESULT.md)
scored its earlier-data-conditioned forecast at 2.85 m horizontal RMS. The
scientific decision stays **abstain** while the observation-error model is investigated.

[Earlier pilot and all starts](../esa-observed-wide-pilot/README.md) ·
[New six-fit study](RATE_REFIT_V2_RESULT.md) ·
[Shared residual diagnostic](RATE_REFIT_COMMON_RESIDUAL.md).

Sealed earlier manifest/summary SHA-256:
`73aa91117d60ca191f614f0fe826167e8b237fcff320b7676e2f505fd1bf6289` /
`2ce3ae7c4e48adb8d5d3048316a68d88a3015ff1528a3515bb212d1081e15f31`.
Sealed newer manifest/summary SHA-256:
`fabb0ef004ce452a7a0b0a14ac71c307b350d3b9b4d25ca8bc8545598f75c2ba` /
`47f01b56eda5710d0698f26a4727b12945abfcaa8f8fe3be50ff5a8df0fc03a7`.
