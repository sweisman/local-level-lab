# RF04 and the original IMU agree on the scale of whole-second motion

The two GPS receivers supplied positions at all **443 common UTC times**
on the selected stretch. Their horizontal separation was **89.2 m median**
and **91.5 m at most**. Their relative height changes differed by **0.50 m
RMS** after each was referenced to its own first measured height. The
nearly constant horizontal separation is mostly along the path. This
calculation used the
reported timestamps and applied no receiver alignment. [Fixed plan](RF04_MOTION_MATCH_PLAN.md)
· [Receiver offset follow-up](RF04_RECEIVER_OFFSET_RESULT.md)

| Window | Windows | RF04 change, RMS | Group 4 change, RMS | Rotation difference, RMS |
| --- | ---: | ---: | ---: | ---: |
| 1 second | 442 | 0.090° | 0.093° | 0.048° |
| 5 seconds | 88 | 0.281° | 0.280° | 0.081° |
| 10 seconds | 44 | 0.306° | 0.291° | 0.084° |

The table uses the elapsed packet clock and the reported timestamps. Each
window uses the full rotation between RF04 reports and the product of
the Group-4 rotations recorded inside the window. The one-second
difference had a median of 0.027° and a 95th percentile of 0.102°.
All windows met the completeness check, with at most 10 ms of
uncovered edges. The nominal 200 Hz clock gave nearly identical results.

Moving the Group-4 windows 80 ms later lowered all three RMS differences.
For one second the difference fell to 0.042°. Moving them 80 ms earlier
raised it to 0.055°. These are fixed sensitivity checks. The data may
reflect timing, filtering and the difference between navigation-frame
and inertial rotation. The analysis keeps all three timing choices.

The comparison checks observed whole-window changes. A fast turn that
reverses inside a second can still be absent from the RF04 endpoint
change. The force-only comparison remains unresolved. The separately
supplied RF04 attitude gives a check on the [saved force predictions](RF04_FORCE_DIRECTION_RESULT.md)
at the reported cadence, with RF04's navigation conventions retained.

One task completed all 21 charged operations with 88,478 selected
Group-4 packets, zero Earth-model fits and zero reserved ESA reads.
Six focused software tests passed. [Saved metrics and receipt](rf04-motion-match-result.json)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_rf04_motion_match report
```
