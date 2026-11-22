# New windows for checking predicted aircraft motion

The previous ESA direction comparisons reused eight windows from recording
187. This selection reserves eight more windows within the same recording,
including four on the flight leg after the Reykjavík stop. A later test can
check how closely the fixed method predicts direction changes on new data
from the same installation.

Use the saved half-minute receiver course summaries. Starting with the
first summary on each leg, divide the usable span into blocks of 420
seconds. Drop a block if it overlaps any of the four earlier development
windows, four turn windows, four steady controls or the staged solver
comparison. Drop any partial block. Retain every remaining block in the
inventory and pick four per leg at the midpoints of four equal chronological
fractions of that leg's candidate list. Use zero-based index
`floor((2*i+1)*candidate_count/8)` for `i` from 0 to 3.

Within each selected block identify 400 receiver queries one second apart,
with at least 10 seconds clear at either edge. Label each block by its
receiver course changes. A bound of 2° or less is steady, a half-minute
span of at least 5° is a turn, and the remainder is intermediate. Course
labels do not control selection. This check needs the saved metadata
only. The later measurement study must verify actual clocks and complete
sensor coverage before scoring.

The selection is disjoint from the identified fit and direction comparison
windows. Other studies have summarized the full recording. These are new
windows for evaluating the direction method within one development
recording. Cross-flight accuracy still requires reserved data.

Freeze the four exact metadata inputs and the source. Run one task, one
charged check, one numerical thread and a 45-second ceiling. The task
reads zero original sensor files and zero reserved flight groups. It
performs no fits. Prepare and verify the receipt from the repository root.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_selection prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run data/esa-direction-holdout-selection-v2 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_direction_holdout_selection report
```

Version 1 stopped before selection because its operation reservation
omitted an explicit zero step count. Its terminal receipt remains sealed.
Version 2 corrects the reservation with the same inputs, rules and limits.
