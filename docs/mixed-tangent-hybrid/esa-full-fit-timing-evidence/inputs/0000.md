# Time both derivative methods on the full ESA development window

The [short timing study](ESA_SHORT_FIT_TIMING_RESULT.md) found a speed gain
with 120 training positions. The [full-window study](OBSERVED_DISPATCH_FRESH_RESULT.md)
verified agreement with 800 training positions and 400 later query times.
Time complete fits on that same full window to check whether the gain holds.

Use the same two settings as the short benchmark, with the archived second
start in both settings. Preserve the prepared increments, training weights,
physical bounds, software, and query times. Use only the decoded training
positions. Keep later receiver positions and reserved flights closed. All
timing results apply to two globe settings on one development flight.

Run the wide method first in the specified-field case and the selective
method first in the zero-field case. Measure process CPU and elapsed time
both for the fit and for the complete calculation including compilation and
forecasting. Allow 40 fit evaluations per method and one native forecast
call per method. Run the two pairs on two one-thread workers. The initial
wall allowance is 10,800 seconds with cooperative checks. Charge before
every native call, and preserve any incomplete or failed outcomes.

Require original numerical stopping, all columns retained, matching
training costs within relative `1e-8` and paths within 10 mm. Compare each
new result with its own archived fit and forecast on the full grid. Use the
same speed criterion as the short benchmark: both ratios at least one and
their median greater than 1.25. Report all times even if the gate fails.

The canonical status tool reads the saved locks, completed pairs and charged
calls. Use the qualified `lll.studies.task_resume` workflow after a technical
interruption. Preserve the same scientific task identities and inputs.
Allow at most two attempts per task, two recorded technical interruptions,
up to 10,800 seconds for recovery, and require at least
1 GiB free storage. Seal the interrupted original before freezing recovery.
Run `lll.esa_full_fit_timing recover` to verify the original and continue only
unfinished tasks. A completed pair is never rerun.
