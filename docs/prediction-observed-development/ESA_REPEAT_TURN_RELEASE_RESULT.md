# Releasing the ESA turn forecasts for scoring

The four windows on ESA development flight 187 completed training in all
16 starts. The forecast gate released eight predictions for scoring.
Each has two fixed error descriptions and two starting points, for 16
fits in total. The original freeze was never started. Its input check
would have refused the metadata added during reboot recovery. The
replacement adapter accepts that metadata and gives the original
forecast calculation the same training inputs as before.

Seventeen software tests passed. They check recovery accounting,
forecast seals, the fixed scoring rule, and the order in which the
software may read receiver observations. A check on the prepared
study also confirmed that the scoring program stopped before opening
later positions while the fits were unfinished.

Scoring requires a terminal record for every start, including numerical
failures. For each window and error description, the lowest converged
training cost selects the forecast. Start 0 wins a tie. If the selected
start did not save a forecast, that comparison has no score. A separate
receipt records these choices and verifies the forecast seals before the
program decodes later GPS positions. The scores measure how well the
forecasts predict positions on this development flight.

The replacement manifest SHA-256 is
`d9e63245684806e14fc3ac253ad0b98cfdbbb21fa831f348c344c58a6715bdd8`.
It retains the original task set, input files, and work limits. At
preparation it had zero charged starts and zero completed fits.
It closed in 75.7 minutes with **16 passing starts and zero errors**.
The [scored forecasts](ESA_REPEAT_TURN_FORECAST_RESULT.md) show later
three-dimensional root-mean-square position errors of **0.44–1.97 m**.
Allowing for additional error during turns improved the score in all
four windows. Adding the steady allowance as well gave the best score in
three windows. Both allowances leave the point forecast unchanged.
Even the best-scoring allowance underestimates the observed error spread
in some windows. These windows come from one development recording.
The [runtime evidence](esa-repeat-turn-forecast-evidence/runtime/README.md)
preserves the sealed run. The archive check recovered and verified all
eight forecast hashes against the scores.

Use the [status command](../../analysis/STATUS.md) with
`--study data/esa-repeat-turn-forecast-v2`. Run the two scoring commands
only after all 16 starts have reached a terminal outcome.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 4 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_release release \
  --manifest-sha256 d9e63245684806e14fc3ac253ad0b98cfdbbb21fa831f348c344c58a6715bdd8
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 4 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_release score \
  --manifest-sha256 d9e63245684806e14fc3ac253ad0b98cfdbbb21fa831f348c344c58a6715bdd8
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 4 --threads 1 -- ~/venv/bin/python -m lll.esa_repeat_turn_report \
  --manifest-sha256 d9e63245684806e14fc3ac253ad0b98cfdbbb21fa831f348c344c58a6715bdd8
```

The report command verifies the saved selection and score receipts and
lists the result for every window and error description. It runs no
additional fits and reads no receiver positions.

After an actual interruption, check the study with `--recovery`. When
the coordinator and its workers have stopped and the recovery check
identifies unfinished tasks, use the [shared recovery procedure](../../analysis/STATUS.md)
with the paths below. The recovery plan retains every sealed scientific
result and charges any restarted task against the separate allowance.

| Recovery setting | Value |
| --- | --- |
| Original study | `data/esa-repeat-turn-forecast-v2` |
| Recovery study | `data/esa-repeat-turn-forecast-v2-recovery` |
| Recovery proof | `docs/prediction-observed-development/esa-repeat-turn-recovery-qualification.json` |
| Starts per task, including the original | 2 |
| Maximum technical interruptions | 4 |
| Wall time | 14,400 seconds |
| Free disk reserve | 2,147,483,648 bytes |

[Software qualification](esa-repeat-turn-release-qualification.json) ·
[Test report](esa-repeat-turn-release-tests.xml) ·
[Original execution freeze](ESA_REPEAT_TURN_EXECUTION_RESULT.md)
