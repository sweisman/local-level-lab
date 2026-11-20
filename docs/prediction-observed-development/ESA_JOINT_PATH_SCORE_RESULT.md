# The whole-path score separates forecasts whose ranges overlap

On ESA development recording 187, the specified-field globe had the lowest
whole-path error in both complete settings. This held with either receiver
weighting and with or without the changing-jerk term. Under the full law, all
pointwise ranges overlap. The whole-path calculation detects sustained
differences by accounting for which errors tend to occur together over time.

| Candidate | Scored starts | Standardized RMS over 120 later reports, full law | Reduced law |
|---|---:|---:|---:|
| Globe with specified field | 8 | 0.14–0.17 | 0.14–0.18 |
| Globe with zero field | 8 | 1.20–1.27 | 1.32–1.40 |
| Stationary flat disc | 4 | 1.53–1.56 | 1.68–1.70 |

The ranges in the table span both receiver settings. A lower value means a
smaller joint error under that law. Four flat-disc starts failed their
original numerical checks, so two of the four matched settings remain
incomplete. The fitted paths, training-start rule and later GPS inputs were
held fixed.

For comparison, the same full-law calculation gave standardized RMS between
0.82 and 1.12 on the 256 saved, known-answer generated histories. The reduced
law had a worse Gaussian forecast score in 197 of those histories. The
generated controls start from known initial conditions and use shorter
training and prediction intervals. Their scores cannot calibrate a cutoff
for the ESA flight, and the very low specified-field globe score is evidence
to check the uncertainty scale. The ESA results are development rankings
from one flight. All seven reserved groups remain closed.

A [separate known-model replay](MATCHED_GENERATED_JOINT_SCORE_RESULT.md)
recovered 9–12 of 12 generating labels depending on the receiver and drift
assumptions. The differences show why both recovery and error scale need
testing before freezing a decision rule.

The conditional score agrees with a direct dense calculation. Replays read
sealed fits and error paths and perform no new fits or simulations. Run from
the repository root, then repeat with `generated` as the final argument.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.esa_joint_path_score observed
```

[Fixed method](ESA_JOINT_PATH_SCORE_PLAN.md) · [Frozen inputs](esa-joint-path-score-freeze.json) ·
[Observed scores](esa-joint-path-score-observed.json) · [Generated scores](esa-joint-path-score-generated.json)
