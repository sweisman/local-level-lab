# First ESA conditional-forecast attempt stopped at its work limit

The one preselected development task reached its frozen ceiling of 600,000
native calls before the full error operator finished. It used about 433 million
of its allowed 6 billion packet visits. The task is **terminal and retained**;
no later GPS position was opened and no conditional forecast was scored.
The scientific decision remains **abstain**.

The work limit was too tight because the implementation rebuilt the error
operator once for the 800 early GPS epochs and again for the full 1,200-epoch
interval. Each IMU packet causes at least one native call, with extra calls at
GPS query times. A separately frozen method can build the full operator once,
verify that its 800-epoch prefix matches the sealed training operator, and
condition it on the same saved early errors. That avoids repeating the packet
history. It must keep the same data, model and error law, and receive its own
finite allowance; the failed task will not be resumed or relabeled.

The [fixed question](CONDITIONAL_FORECAST_PLAN.md) and sealed task preserve the
original limit and failure. No ESA confirmation group was opened.
