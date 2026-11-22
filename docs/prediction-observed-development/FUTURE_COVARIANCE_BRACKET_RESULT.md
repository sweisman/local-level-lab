# A declared range of later error changes

An earlier forecast can keep its fitted mean and still allow a change in
the amount and pattern of later error. The new software uses a declared
range of additional receiver scatter and drifting position offset after
the cut. It calculates the best and worst whole-path scores across that
range, including uncertainty from estimating the earlier calibration.

| Generated later error | Fixed law inside reference | At least one allowed covariance inside | Every allowed covariance inside |
|---|---:|---:|---:|
| No increase | 242/256 | 247/256 | 51/256 |
| One quarter of the added covariance limit | 175/256 | 255/256 | 79/256 |
| At the limit | 18/256 | 252/256 | 15/256 |
| Nine times the limit | 0/256 | 3/256 | 0/256 |

All 768 in-range scores lay within the calculated extrema when checked
against an independent dense calculation. The wider range protects
against rejecting the correct forecast under a supported change. It
also makes absolute fit harder to establish when the actual covariance
is unknown. In the interior case, a deliberately wrong alternating
four-metre signal was above the reference for every allowed covariance in
164 of 256 paired checks. These counts apply to the declared controls.

The two endpoints bound the score because adding positive semidefinite
covariance reduces the squared standardized error at a fixed mean.
Independent changes after the cut preserve the earlier fit and its
conditional forecast mean. The reference assumes an affine mean, a
Gaussian error law and a common overall scale estimated from earlier
residuals. The bracket allows the covariance pattern to change as well.

Aircraft work still needs an independent basis for the size and structure
of the permitted increase. The opened ESA flight showed that a previous
error scale can be too small. Its score ratio alone cannot determine
whether receiver error, inertial drift or calibration explains the
change. This control made no aircraft decision.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.future_covariance_bracket_control replay
```

[Fixed design](FUTURE_COVARIANCE_BRACKET_PLAN.md) ·
[Frozen inputs](future-covariance-bracket-freeze.json) ·
[Full control counts](future-covariance-bracket-result.json)
