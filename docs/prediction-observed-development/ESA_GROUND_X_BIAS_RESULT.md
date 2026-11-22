# Ground stops favor a smaller X-axis accelerometer bias

The two stationary intervals also put pressure on the **+0.10 m/s²
X-axis bias** that reversed the gyro-direction comparison. With
one shared accelerometer calibration and a separate unknown force
level at each stop, the lowest-spread correction uses an X bias of
**+0.019 m/s²**. Fixing it at +0.10 m/s² worsens the spread even
when the other accelerometer terms are allowed to adjust.

| Shared calibration across the stops | First stop half-range | Second stop half-range |
| --- | ---: | ---: |
| No correction | 0.000306 m/s² | 0.000082 m/s² |
| All accelerometer terms free | 0.000205 m/s² | 0.000091 m/s² |
| X bias fixed at +0.10 m/s², other terms free | 0.000391 m/s² | 0.000267 m/s² |

The calculation minimizes the worst within-stop spread in squared
force. The table expresses the resulting spread as half the range
of force magnitude. Fitting either stop alone gives the same direction
of change when X is fixed at the endpoint. The free calibrations
also use gain or bias bounds on other axes.

All 75 minute averages came from the previously selected ground stops.
The analysis supplies no gravity value, uses no Earth-model fit and
needs no assumption about the sites having the same gravity. It
cannot separate small aircraft movements, temperature effects and
measurement error. The ground data therefore favor a smaller X bias
without independently excluding the endpoint.

Two tests passed. All six linear programs completed and the corrected
force spreads were verified. The first frozen attempt failed before
any program started because its wrapper did not convert the input
vectors to arrays. The corrected freeze preserves the same data
and scientific comparison. No original data or reserved recordings
were opened.

From the repository root, with the sealed ground stop and calibration
reports in place,

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_ground_x_bias freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_ground_x_bias run
```

[Frozen plan](ESA_GROUND_X_BIAS_PLAN.md) ·
[Calibrations, force spreads and hashes](esa-ground-x-bias-result.json) ·
[Preserved technical failure](esa-ground-x-bias-v1-failure.json) ·
[First source version](esa-ground-x-bias-v1-source.py.gz)
