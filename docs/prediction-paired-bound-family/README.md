# Paired error-law interval study

**Complete: all 24 generated recordings passed the technical gate.** The study contains 24 generated recordings
and two fits per recording. It tests whether keeping both plausible IMU error
laws produces earlier-only uncertainty intervals that contain later physical
positions and later receiver reports. It does not fit an observed flight or
choose an Earth model.

The source and numerical environment are fixed in the prepared study. Eighteen
focused software checks and seven interruption-recovery checks passed. The
separate saved-result audit passes eight checks, including a full 24-case
sealed-result replay and a tampered-score rejection. It independently recounts
interval containment from sealed later truth and reports both recording-level
and coordinate-level totals; the [verified result](RESULT.md) is published. The
limits are 200 evaluations per fit, 479,632 native calls per recording and a
five-hour cooperative wall time with four single-thread workers. The study
started after the ESA three-pair run released its threads. The original allowance
sealed 20 passing recordings and four technically interrupted starts. A separate
continuation is computing exactly those four with the original measurements,
method and per-recording ceilings. A first continuation preparation stopped
before any new fit because its source list repeated paths already frozen in
the original study; the corrected launcher passed seven recovery checks before
the replacement continuation started. That continuation sealed all four remaining
recordings, and the combined identity ledger verifies 24/24 passing results
without repeating a completed recording. The runner reserves
each task's full native-call ceiling before computing; the charged-call count
therefore is not a count of completed calculations. The
[frozen plan](PLAN.md) gives the condition matrix and acceptance rules.

All 48 two-law fits passed numerical stopping and the physical prediction
screen. Both interval unions contained every withheld coordinate in all 24
recordings. This remains a method check. It is too small to establish 95%
prediction coverage or a threshold for real aircraft.
