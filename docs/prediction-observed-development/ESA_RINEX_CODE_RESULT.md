# ESA GPS code reconstruction

The GPS code measurements from development recording 187 yielded positions at
all **1,041 half-second epochs** under both fixed methods. Each solution used
11–12 GPS satellites. The median difference between the two reconstructions
was **2.08 m horizontally**. The dual-frequency solution was **1.34 m lower**
at the median.

| Code method | Positions solved | Median within-epoch range RMS |
| --- | ---: | ---: |
| L1 code with broadcast ionosphere correction | 1,041 / 1,041 | 0.78 m |
| L1 and L2 code combined | 1,041 / 1,041 | 1.70 m |

The dual-frequency method used C2W for 12,316 satellite observations and
C2X for 38. These differences and range residuals describe two position
calculations from the same antenna. They do not establish either method's
absolute position accuracy. The reconstruction used the RINEX header point
to start each solve. It used no inertial measurements or exported receiver
positions. The seven reserved ESA groups remain sealed.

The saved positions precede any comparison with the receiver export. The
next check can compare them over matched GPS times to quantify sensitivity
to the measurement and processing choices.

Run the commands from the repository root with the
[verified AIR1 excerpt](ESA_RINEX_WINDOW_RESULT.md) and the broadcast
navigation product in their recorded locations.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_rinex_code_study freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_rinex_code_study run
```

The sealed local result is in
`data/external-imu-survey-20261018/esa-sample/rinex-400-120-stream/code-position/`.
The position rows have SHA-256
`02b904918d6bd835d94ef8d0987d1d1180312cbf486870d37293a24756cadc63`.
The freeze has SHA-256
`0f498b01188e94af1abc04b40d25bb0fe3c279ba3808c3a678a8c5b696cd7460`.

[Frozen method and limits](ESA_RINEX_CODE_PLAN.md)
