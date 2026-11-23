# The reserved ESA flights support matched prediction times

This check used every half-second receiver report. The
[follow-up](ESA_CONFIRMATION_CADENCE_RESULT.md) checks the one-second
cadence used in the development fits.

**All seven reserved groups support both training lengths on the same
withheld receiver reports.** Each layout uses an already timing-verified
20-minute slice. The shorter layout uses the last 400 of the longer
layout's 800 training reports. Both withhold the same next 120 reports.

The short and long training sets span about 199.5 and 399.5 seconds.
The 120 withheld reports span 59.5 seconds. The largest receiver gap
across the selected queries was 0.500002 seconds, rounded up, below the
0.75-second limit. The original receiver bytes matched the acquisition
hash for each of the seven groups.

The check saved the group identities, receiver indices, time ranges and
time-list hashes. It ran zero fits and opened zero inertial values or model
outcomes. The layouts remain available for a later frozen protocol. The
verified timestamps establish data support. The choice of training length,
aircraft error law, and independent prediction-accuracy rules remain open.

[Fixed plan and commands](ESA_CONFIRMATION_QUERY_PLAN.md) ·
[Original IMU timing check](ESA_CONFIRMATION_TIMING_RESULT.md) ·
[Freeze](esa-confirmation-queries-v1-freeze.json) ·
[Time-window ledger](esa-confirmation-queries-v1-result.json).
