# ESA forecasts scored against rebuilt GPS positions

Both GPS code reconstructions give the same forecast ranking as the original
receiver export. The specified-field globe has the lowest error and passes
the existing position-accuracy screen in all four available comparisons
from the two complete model settings and the two GPS code methods.

| Position reference | Specified-field globe | Zero-field globe | Stationary disc |
| --- | ---: | ---: | ---: |
| Original receiver export | 5.23 m | 2,590.07 m | 3,998.25 m |
| L1 code reconstruction | 4.96 m | 2,590.79 m | 3,999.21 m |
| L1 and L2 code reconstruction | 6.74 m | 2,590.01 m | 3,998.63 m |

These are total position RMS errors over the same 120 later reports in the
increment error convention. The point convention gives the same ranking.
The two previously incomplete settings remain unresolved. No forecast was
propagated again and no model was refitted.

| Code path compared with the original export | Earlier horizontal / height RMS | Later horizontal / height RMS |
| --- | ---: | ---: |
| L1 | 1.72 / 2.13 m | 1.51 / 2.15 m |
| L1 and L2 | 1.20 / 1.49 m | 1.97 / 1.68 m |

All 520 paired positions use the same epoch assignments with and without
the receiver clock correction. The maximum time mismatch drops from
0.500 ms to 0.157 µs with the correction. The comparison supports
robustness to these GPS processing changes on one development flight.
The reconstructions share the antenna and GPS observations with the
original export. Absolute airborne position accuracy and a flight-level
decision threshold still need separate validation. The seven reserved
ESA groups remain sealed.

## Reproduce the comparison

To check the tables from the saved reports, run this from the repository root.
It verifies the result and freeze hashes, recomputes the receiver differences
table from the signed errors, and checks the forecast rankings and accuracy
flags from the saved scores. It uses the three report files in this directory
and requires no source recordings or study catalog.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_code_receipt_audit
```

To recompute the forecast errors from their original positions, use the
full replay described below.

The [source and bindings archive](esa-rinex-code-comparison-freeze.zip) contains
the frozen dependencies that differ from the public checkout and the two
study manifests. Extract it into a disposable checkout. A full rerun also
requires the local sealed 400/120 and 800-report parent studies. Their exact
manifest hashes are in the archive. The public checkout currently supplies
the code, signed differences and scores. It needs those local study inputs
to rerun the comparison from positions.

With the local inputs in place, reproduce the
[GPS code reconstruction](ESA_RINEX_CODE_RESULT.md) and run both commands
from the repository root. The scorer verifies the fitted forecast hashes and
the source of the matched receiver positions.

```sh
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_rinex_code_comparison freeze
~/venv/bin/python analysis/tests/run_numerical.py --threads 1 -- ~/venv/bin/python -m lll.esa_rinex_code_comparison run
```

[Frozen comparison plan](ESA_RINEX_CODE_COMPARISON_PLAN.md) ·
[Signed differences, scores and hashes](esa-rinex-code-comparison-result.json)
