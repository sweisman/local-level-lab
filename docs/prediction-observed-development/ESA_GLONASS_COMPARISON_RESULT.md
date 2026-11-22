# ESA forecasts scored against a different satellite constellation

Both GLONASS position calculations preserved the ranking on the same
120 later reports. The specified-field globe had the smallest error
and passed the existing position-accuracy screen in all four comparisons
from the two complete model settings and the two GLONASS code methods.

| Position reference | Specified-field globe | Zero-field globe | Stationary disc |
| --- | ---: | ---: | ---: |
| Original receiver export | 5.23 m | 2,590.07 m | 3,998.25 m |
| GLONASS L1 code | 8.12 m | 2,593.07 m | 4,001.70 m |
| GLONASS L1 and L2 code | 7.09 m | 2,588.81 m | 3,997.23 m |

The table shows total position RMS for the increment error convention.
The point convention gives the same ranking. The two previously
incomplete model settings remain unresolved.

Both methods solved **1,041 of 1,041** epochs using 7–8 satellites.
Compared with the original export, the L1 positions differed by
3.37 m horizontal RMS and 1.86 m height RMS over the later reports.
The L1 and L2 combination differed by 2.87 m horizontally and 5.78 m
in height. The dual-frequency result has a mean height difference of
+4.10 m. The code-only solutions do not resolve satellite or receiver
channel biases, and neither path establishes the absolute position error.

The GLONASS reconstruction uses a different set of satellites from the
earlier GPS reconstruction. The antenna, flight and fitted forecasts
are shared. The L1 calculation uses GPS broadcast ionosphere
coefficients. The dual-frequency calculation instead combines the two
GLONASS codes to cancel first-order ionosphere delay. No Earth-model fit
or forecast ran again. The seven reserved ESA groups stayed closed.

The orbit tests agreed within 2 cm with a separately integrated
inertial-frame reference over ±15 minutes. The receiver control
recovered the generated position and clock within 10 µm in range units.
Seventeen focused tests passed.

## Reproduce with the sealed local inputs

Use the verified AIR1 excerpt and broadcast navigation file from the
[GPS reconstruction](ESA_RINEX_CODE_RESULT.md). The comparison also
uses its saved GPS-time matches and the local sealed 400/120 forecast
and 800-report parent studies. Their hashes are in the machine result.
The orbit and receiver controls are in
`analysis/tests/test_glonass_code.py`.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_glonass_code_study freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_glonass_code_study run
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_glonass_comparison freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_glonass_comparison run
```

[Reconstruction method](ESA_GLONASS_CODE_PLAN.md) ·
[Scoring plan](ESA_GLONASS_COMPARISON_PLAN.md) ·
[Per-epoch differences, scores and hashes](esa-glonass-comparison-result.json)
