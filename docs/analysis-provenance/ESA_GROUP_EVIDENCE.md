# ESA forecasts by flight group

The ESA forecast results indexed here all use **recording 187**. It is one
development group. Seven other groups, covering eight recorder files, are
reserved for a later confirmation test. The two files labeled 178a and 178b
belong to the same reserved group.

The [receiver-row table](esa-forecast-cuts.csv) traces 14 scored cuts and
three selected candidates awaiting evaluation. It gives the exact earlier
and later rows from the receiver file. Rows are counted from zero. Each cut
uses every second row in the stated range, about one position per second.

| Study | How to count its evidence |
|---|---|
| [First twenty-minute pilot](../esa-development-pilot/README.md) and [revised fit](../esa-observed-wide-pilot/INTERPRETATION.md) | Both use the same 800 training and 400 later positions. The original had 15 of 24 qualified starts and the revision had 22 of 24. |
| [Shorter cuts of that interval](../prediction-observed-development/ESA_RAW_ACCURACY_RESULT.md) | The cuts after 200, 400 and 600 reports test positions used for training in the 800-report fit. The cut after 800 tests the first 120 positions of its 400-position forecast. The [matched three-candidate test](../prediction-observed-development/ESA_400_120_MODEL_MATRIX_RESULT.md) reuses the 400/120 cut. |
| [Four turns and four steady windows](../prediction-observed-development/ESA_MATCHED_CONDITIONING_RESULT.md) | These add separate times on recording 187. Raw, adjusted and [timing-shift](../prediction-observed-development/ESA_FORECAST_TIME_SHIFT_RESULT.md) results reuse the same later positions within each window. |
| [Later twenty-minute comparison](../mixed-tangent-hybrid/ESA_DISPATCH_ACCURACY_RESULT.md) | Both solvers, both globe variants, the error assumptions and alternate starts reuse one 400-position later path. Four of 16 primary forecasts meet all fixed limits at this horizon. |
| [Three selected short-block candidates](../esa-short-block-development/README.md) | These are metadata selections with no fit in this index. They also belong to recording 187. |

Counting each scored cut once gives 2,240 later positions. Counting each
original receiver row once gives **2,120**, of which **360** also occur in
another cut's training interval. Every reported fit retains its own
earlier/later separation. The shorter cuts help explain how forecasts behave
on this flight. Their outcomes share a recording and partly reuse its data.

On the twelve 120-position checks, **9/12** unadjusted windows met the fixed
position limits under both inertial error descriptions. **11/12** met them
under both after adjustment from earlier information. One of the two
adjusted paths is unavailable in the remaining window. These counts reuse
the same receiver positions before and after adjustment. They describe
accuracy on the development recording. Aircraft error coverage and
independent confirmation remain open.

Run this from the repository root to verify the table and its receipt against
the saved reports and group ledger. It requires no original recordings,
numerical fits or archive restoration.
The check also passed from a separate directory containing only the named
reports, generated table, receipt and six Python files, with no installed
numerical packages in the verification process.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_group_evidence check
```

[Hashes and group assignments](esa-group-evidence-receipt.json) ·
[NASA group ledger](NASA_GROUP_EVIDENCE.md) ·
[Independent-flight decision rule](../FLIGHT_GROUP_DECISION.md)
