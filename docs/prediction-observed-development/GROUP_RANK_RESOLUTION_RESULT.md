# How many model simulations would a flight-level test need?

The saved comparison has twelve generated flights and one draw in each
fixed combination of physical model, route and IMU noise law. With one
reference draw, the smallest possible rank p-value is **0.50**. Even if
the four draws per physical model were interchangeable, which the study
design does not establish, the best possible p-value would be **0.20**.
The existing comparison can check rankings and reveal ambiguities. It
cannot supply the reference samples for the flight-level decision.

The table gives illustrative minima for seven flight groups and an overall
5% error allowance. Counts are per declared null scenario. They apply only
when the target score exceeds every available reference score.

| Required qualifying groups | p-value needed within a group | Draws if all available | Draws with one unavailable |
|---:|---:|---:|---:|
| 1 | 0.00714 | 139 | 279 |
| 3 | 0.01000 | 99 | 199 |
| 5 | 0.01667 | 59 | 119 |
| 7 | 0.05000 | 19 | 39 |

## How the within-group test works

Each reference draw runs the same group procedure as the target. Count
reference scores at least as extreme as the target, add one, then divide
by the number of planned draws plus one. Ties and unavailable draws count
against rejecting the model. If the model allows several error scenarios,
the largest p-value protects any scenario that could be true. A scenario
without a usable target or reference cannot support rejection.

The tests verify the finite rank calculation with tied scores and missing
draws, and its combination with a rule that permits dependence among flight
groups. They also verify the transition from 98 to 99 draws in the
illustrative three-group rule. The formula requires exchangeability
between the target and references within the correct scenario and
protects only the declared family of scenarios. The aircraft error law
and the full set of plausible scenarios remain open. No confirmation
threshold was selected and no protected flight was opened.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.group_rank_resolution_report replay
```

[Fixed design](GROUP_RANK_RESOLUTION_PLAN.md) ·
[Frozen inputs](group-rank-resolution-freeze.json) ·
[Complete counts](group-rank-resolution-result.json)
