# Inventory repeat turns without using model results

Use both receiver-selected full-motion runs in opened ESA recording 187.
Exclude the first 2,400 indices of the first run, which contain the
previously scored 20-minute development portion. Exclude the complete
supports of all three preselected short-block windows. These exclusions
define a separate development inventory and do not change prior selections.

In each remaining contiguous run, form consecutive 60-report blocks
at the original 2 Hz rate. Apply the [existing turn and straight-control
screen](ESA_MANEUVER_PAIRS_PLAN.md), which requires a course span of at
least 5° for a turn and at most 2° for each quiet neighboring block.
Keep a possible forecast for each matched turn only when the full
400-second training and 120-second scoring support fits inside the
retained run. The turn starts 30 seconds after that boundary. Record
chronologically non-overlapping supports, including the earlier
turn/control matches that lack sufficient forecast support.

Allow one receiver scan with a verified source hash and at most 64,080
reports. Use one numerical thread. Read no model residuals, IMU samples
or reserved flights. Counts describe repeat opportunities on one flight.
A new forecast would still need a separate qualified execution freeze.

The same software check uses known-answer data with a repeated maneuver,
then reverses the second response and changes the drift after the cut.
Both cases have the same earlier observations. This tests that the
earlier-only correction transfers when its assumptions hold and that the
later scoring can expose a change. It establishes no aircraft coverage.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turns freeze
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turns replay
```
