# Six wider-arithmetic forecasts passed the recorded-data checks

Six of the eight planned cases reproduced their training trajectories and
passed the numerical stopping check. The 30-minute study closed after
charging 103 of 248 allowed native evaluations. Both recordings remain
incomplete for the four-model comparison.

| Recorder | Candidate | Training evaluations | Later horizontal RMS | Later height RMS |
|---|---|---:|---:|---:|
| IMU8 | Globe, specified field | 9 | 19.36 m | 10.49 m |
| IMU8 | Globe, zero field | 17 | 1,363.43 m | 24.39 m |
| IMU8 | Disc, specified field | 13 | 242.51 m | 22.22 m |
| IMU8 | Disc, zero field | 30, stopping check failed | No forecast | No forecast |
| IMU21 | Globe, specified field | 7 | 2.18 m | 5.05 m |
| IMU21 | Globe, zero field | 11 | 134.97 m | 7.64 m |
| IMU21 | Disc, specified field | 10 | 70.07 m | 8.28 m |
| IMU21 | Disc, zero field | Unstarted | No forecast | No forecast |

The table uses the onboard receiver for scoring. The two reconstructed GPS
streams give the same order among the three available candidates on both
recordings. These are withheld forecasts for an exploratory software check.
The gap in the zero-field comparison and the unqualified aircraft error
model keep the overall result at abstain.

The largest difference between a saved forecast's training prefix and the
fitted path was 2.29 × 10⁻¹⁴ m. The verifier checked each of those six paths
and rescored its later part against all three receiver streams. It also
checked the frozen sources and evaluation charges. The two receiver
reconstructions share satellite observations with the onboard solution.

The IMU8 zero-field disc fit saved its endpoint after 30 evaluations. The
fresh correction changed training cost by 1.15 × 10⁻⁷ relative, above the
frozen 10⁻⁸ limit, so the failed stop remains. Its forecast could not start
before the deadline. Only one of 67 training evaluations across the six
passing fits visited a trial point that was never accepted. The failed disc
fit spent 18 of 30 on such points. This identifies where a value-only trial
check might help and where it would add work.

The [frozen plan](MATCHED_OBSERVED_NUMERICAL_PLAN.md), [forecast table](matched-observed-preflight-fits.csv)
and [replay receipt](matched-observed-preflight-receipt.json) preserve the
protocol and all available scores. The unstarted case and failed stopping
check remain in the [sealed record](../ilvis0-matched-observed-preflight-runtime/README.md).
The next method check should compare exact
value-only and wider tangent residuals before testing any faster fit.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_matched_observed_preflight_report
```
