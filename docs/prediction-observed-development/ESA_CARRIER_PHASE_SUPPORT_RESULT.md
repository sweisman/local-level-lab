# GPS carrier phase is continuous over the later ESA comparison

The frozen continuity screens retained at least five GPS satellites in
**1,039 of 1,040** adjacent half-second pairs. They retained 12,423
L2W and 34 L2X satellite pairs, each with continuous L1 C/A phase.

At GPS-week seconds **388555.5–388556.0**, all 12 L1 phase changes disagreed
with Doppler by about 1.575 million cycles. This coincided with a change
of nearly 1 ms in the reported receiver clock offset. The gap is kept.
The preflight establishes the timing association and leaves the receiver
processing cause open.

The gap occurs before the 400/120 training cut. All 240 half-second pairs
from the last earlier report through the last later report pass the
minimum-satellite requirement. The supported segment can therefore be
checked as one path from the earlier position anchor. A whole-window
carrier reconstruction would need a separately qualified clock-step
correction or a separate anchor across the gap.

A [separate clock check](ESA_CARRIER_CLOCK_STEP_RESULT.md) subsequently
found that all 12 satellites pass the original continuity screens once
the recorded step is accounted for.

The preflight made zero receiver-position solves and zero inertial fits.
It checked signal continuity before a separate geometry and displacement
check, with the seven protected flights still sealed.

[Method and fixed thresholds](ESA_CARRIER_PHASE_SUPPORT_PLAN.md) ·
[Continuity freeze](esa-carrier-phase-support-freeze.json) ·
[All 1,040 pair dispositions](esa-carrier-phase-support-result.json)
