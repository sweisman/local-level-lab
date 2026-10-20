# Longer complete prediction comparison

This generated-data study extends the complete common-acceleration comparison
from 1.8 to 7.2 seconds. It follows successful execution and exact native
compatibility qualifications. No original aircraft measurements, observed fits
or protected ESA confirmation outcomes are used.

Use all six physical-model/processing cases and all eight original orientation
sectors, retaining the same 27 physical bounds and 15 common-error variables.
Reuse the exact 1,600-packet inputs from the completed duration screen. Training
times are 0.8, 1.4, 2.4, 3.6, 4.8 and 6 seconds; the unused future epoch is
7.2 seconds. These are the short study's times multiplied by four, with the
same generated trajectory and known calibration vector. Keep the original
1 mm generated observation allowance and 10 micrometre arithmetic margin.

Training contraction and future prediction use the unchanged qualified
42-column experiment. The same common-error vector applies at every epoch.
Future truth is unavailable until the training constraints and future envelope
have been saved. Keep excluded sectors and known-truth containment checks.

Pass conditions are unchanged numerical consistency, retention of the known
truth where it lies in the sector, and containment of its future position.
Require every preselected identity and all six complete sector unions. Report
the union widths and growth relative to the short study; do not invent a
receiver-accuracy threshold or claim that passing software controls establishes
useful recording-scale uncertainty. These bounds are generated prediction
ranges, not measured aircraft errors or calibrated confidence intervals.

Finite allowance: 48 identities, at most three native calls and eight bounds
per identity; 144 native calls, 230,400 packet visits, 384 bounds and 614,400
reserved bound steps in total. Four workers use one numerical thread each.
The wall allowance is 5,400 cooperative seconds, with 120 cooperative seconds
per bound. There are no retries, process signals or allowance extensions.
The serial short-study timing projects approximately 96 minutes of aggregate
work, or roughly 25 minutes with four workers; this is an estimate, not a limit.

Freeze source, input, environment/compiler identity, all tasks, allocation and
these rules before execution. Preserve incomplete/failed identities. Only
verified publication can inform the next recording-scale feasibility gate.
