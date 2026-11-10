# Calibration ended after an execution interruption

**All 1,813 completed simulated forecasts pass the independent numerical and
position-error checks.** Four charged starts were interrupted before a result
was saved. No completed numerical failure was found.

| Disposition | Fit attempts |
|---|---:|
| Completed and passing | 1,813 |
| Interrupted | 4 |
| Not executed; allowance closed unused | 5,359 |
| Planned | 7,176 |

The phase closed after 38.7 hours. Work was returned from 79 of the 299 planned
noise families; settings and starting points within a family are related,
not independent trials. Each candidate fits its own generated truth. These
numbers are not additional flights or votes for an Earth model.

## Why there is no threshold

Both prescribed starts of one required setting were interrupted: the
increment-input stationary-globe case with `profile=true` in family
281474977410729.
The other two interruptions affect separate settings. The rule requires the
entire calibration cohort; it does not permit dropping a family or retrying
charged work. The remaining allowance was closed without running more fits.
Independent validation was not launched.

The interruption does not overturn the completed 48-case optimizer
qualification. It prevents this campaign from establishing the planned
prediction-error threshold. Actual aircraft uncertainty and significance
remain unestablished; the original 53 aircraft comparisons are unchanged.

## Reproducibility

The independent audit verifies all 253 frozen sources, the environment,
prepaid work, saved forecasts and native-library identities. Publication
reproduces the saved-only report exactly, with zero new optimizer starts or
native model evaluations. The record preserves 108,936,418 prepaid native calls
and 684,123,672,201 prepaid packet visits, including unfinished work.

The four interrupted starts retain 40 partial files, totaling 597,029 bytes.
They are included in the publication receipt as unfinished evidence, not
completed forecasts. The interruption audit and partial-file inventory are
preserved with the publication artifacts.

The frozen reporter's `cohort_interrupted` flag covers cooperative stops and
does not count this runtime interruption. The four sealed outcome statuses
and companion interruption inventory record it explicitly. The separate
complete-cohort check rejects a calibration handoff regardless of that flag.
The original report is preserved unchanged.

The [recovery plan](../CALIBRATION_RECOVERY_PLAN.md) requires reliable execution
before another large campaign. No method, bound or acceptance rule is relaxed.

[All planned attempts](results.csv) · [Original finite plan](PLAN.md) ·
[Current status](../FEASIBLE_PREDICTION_STATUS.md).
