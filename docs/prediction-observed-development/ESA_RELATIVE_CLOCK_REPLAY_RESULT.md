# GPS clock changes preserve the ESA forecast ranking

Applying the change over time in final GPS clock corrections moved the
120 positions used to score the forecasts by **0.42 m RMS**. The shift was
**0.32 m horizontally** and **0.26 m in height**, both RMS. All three models
kept the same ranking, and the specified-field globe still met the fixed
position limits under both tested error conventions.

| Receiver solution | Specified-field globe | Zero-field globe | Stationary disc |
| --- | ---: | ---: | ---: |
| Original broadcast solution | 6.739 m | 2,590.011 m | 3,998.633 m |
| Broadcast without G17 | 6.757 m | 2,589.800 m | 3,998.425 m |
| Clock changes, same set without G17 | 6.754 m | 2,589.477 m | 3,998.108 m |

The table gives total position RMS for the increment error convention.
Removing G17 alone moved the reference path by **0.37 m RMS**. The clock
comparison then reused exactly the same reduced satellite set. Both arms
kept the broadcast orbits, observed dual-frequency code and original
transmit times. Estimated clock differences were measured relative to G01
and anchored at the first observation of each satellite. This tests clock
variation over the window. Constant offsets and other common receiver
errors still need independent evidence. [Available clock data](ESA_PRECISE_GPS_SUPPORT_RESULT.md)

Both arms completed all **1,041** epochs in **56 seconds**. The ledger
charged 2,082 starts and reserved 9,369 range evaluations. The successful
replay used 7,260 of those evaluations. The rescore used the two existing
complete forecast settings and verified the original broadcast scores.
No new inertial fits or forecast propagations ran. The seven reserved ESA
flight groups remained sealed.

## Reproduce the tables

With the sealed receiver excerpt, GPS products and saved broadcast solution
in place, prepare and run in a separate reproduction directory with the
frozen numerical environment. For the closed study, use only the last
command. The scoring step needs the same sealed earlier-only forecasts as the
[final orbit replay](ESA_FINAL_ORBIT_REPLAY_RESULT.md#reproduce-the-tables).

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_relative_clock_replay prepare
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.studies run \
  data/esa-relative-clock-replay-v1 --reserved-threads 0
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_relative_clock_score
```

[Frozen method and limits](ESA_RELATIVE_CLOCK_REPLAY_PLAN.md) ·
[Signed position changes, scores and hashes](esa-relative-clock-score-result.json)
