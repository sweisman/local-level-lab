# The RF04 receiver offset follows the direction of flight

At the same reported UTC times, the Applanix GPS positions were **89.2 m
behind** the NCAR reference positions by the median, and **0.21 m to their
left**. The two tracks are close across the direction of travel. The raw
position separation was 89.03 m RMS on the 220 later seconds used below.
[Fixed plan](RF04_RECEIVER_OFFSET_PLAN.md) · [Original matched comparison](RF04_MOTION_MATCH_RESULT.md)

| Description of the offset | Earlier RMS | Later RMS |
| --- | ---: | ---: |
| Unadjusted | 89.74 m | 89.03 m |
| Constant north–east offset | 0.96 m | 0.95 m |
| Relative delay alone | 0.67 m | 0.49 m |
| Constant offset and delay | 0.40 m | 0.86 m |

Each adjustment used the same 219 earlier seconds. The delay-only model
describes the horizontal difference as Applanix positions lagging by
**0.393 s** relative to NCAR positions. It gave the smallest later error
among the three tested descriptions. Allowing a fixed offset as well
changed the fitted delay to 0.887 s and worsened the later error. The
aircraft flew nearly straight, on courses from 177.53° to 177.76° at
224–230 m/s. Changes in earlier velocity represented only 0.43% of its
RMS magnitude, which makes a position offset and a delay hard to separate.

The 0.49 m measures agreement after a relative adjustment using earlier
positions. This leaves the actual timestamp or processing cause open, as
well as absolute position error and any error shared by the receivers.
The saved time tags and orientation comparison are unchanged.

One task completed five charged calculations from saved observations.
No original IMU decode, new Earth-model fit or reserved ESA read was needed.
Four focused checks passed. [Metrics and receipt](rf04-receiver-offset-result.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_rf04_receiver_offset report
```
