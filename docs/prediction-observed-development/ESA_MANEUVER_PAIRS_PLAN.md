# Look for repeat turns in the longer saved ESA forecast

The 400-report holdout after report 800 on ESA recording 187 is
separate from the two 120-report windows used in the first
[motion and error check](ESA_INNOVATION_TRANSFER_RESULT.md).
It is from the same flight and uses a previously scored forecast.

Divide its first 390 reports into contiguous 30-report blocks. Use
original receiver velocity only to classify a turn as a 5° or larger
ground-course span. A straight block has a span no larger than 2°.
For each isolated turn with straight blocks immediately before and
after it, select a nonoverlapping straight triple as a control.
Match by closest block in forecast time, breaking ties by earlier
time. Retain all unmatched turns and the unused 10-report tail.
The 5° and 2° settings separate visible turns for this diagnostic.

Seal motion selections first. Then open the previously saved
conditioned path and report cross-track and height errors for every
block. Compare the before/after cross-track RMS for each matched
turn and straight triple. The receiver velocity defines cross-track
only for this retrospective check and does not change the forecast.
No new fits, original-file reads or reserved flights are needed.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_maneuver_pairs select
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_maneuver_pairs compare
```
