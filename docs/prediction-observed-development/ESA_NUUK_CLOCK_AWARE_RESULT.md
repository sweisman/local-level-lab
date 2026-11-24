# The Doppler check recovered all 20 excluded seconds

The two Nuuk stations could be compared on **all 120 seconds** when each
satellite’s Doppler check used an offset estimated from other satellites.
The earlier check retained 100 seconds. The new check uses the original
phase observations and retains the original lock and two-band checks.
The 994 previously shared range changes reproduced to within
10⁻¹² m after re-centering on their common satellites. [Fixed plan](ESA_NUUK_CLOCK_AWARE_PLAN.md) ·
[Original comparison](ESA_NUUK_NEAR_STATIONS_RESULT.md)

| Compared seconds | Satellite range changes | RMS difference between the two Nuuk stations |
| --- | ---: | ---: |
| Original 100 | 994 | 6.49 mm |
| Newly admitted 20 | 207 | 6.88 mm |
| All 120 under the separate check | 1,236 | 6.54 mm |

The new comparison also adds common satellites on some previously retained
seconds. On the same 1,236 rows, Nuuk Museum differed from Qaqortoq by
7.27 mm RMS and permanent Nuuk differed from Qaqortoq by 3.82 mm RMS.

If both nearby stations observe the same shared range error, shifting the
saved score by its full gap requires at least one of them to have
**5.20 mm RMS** of local error. The earlier 100-second calculation gave
5.78 mm RMS. The station difference alone requires at least 3.27 mm RMS
of error at one station under the same shared-error assumption. These
are lower bounds. The source of the common Doppler mismatch and upper
limits on station and aircraft-specific errors remain open.

The single task completed all 124 charged checks, with zero new aircraft
fits and zero reserved-flight reads. The evidence contains the matched
rows, checked bounds and completion hashes. [Result evidence](esa-nuuk-clock-aware-result.json)

To regenerate the report from the sealed local run, use the following command
from the repository root.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_nuuk_clock_aware report
```
