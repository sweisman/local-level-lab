# Diagonal scaling does not qualify the centered solver

On seven exact linear problems from saved generated-flight derivatives,
the centered solver passed **0/7** with its original coordinates and
**0/7** with diagonal scaling. Each run used 199 evaluations and failed
the unchanged numerical check. This uses the same full calibration box
and all 26 columns in both versions.

| Check | Original coordinates | Diagonally scaled |
| --- | ---: | ---: |
| Range of Jacobian condition numbers | 6.0–306.5 million | 0.69–1.24 million |
| Range of maximum errors from the known target, whitened units | 0.313–0.754 | 0.164–0.547 |
| Required maximum error, whitened units | 0.0001 | 0.0001 |

Scaling improves the condition number on all seven inputs, and reduces
the error on six. The lowest remaining condition number is about 690,000.
Equalizing column norms leaves much of the near-dependence between
calibration directions. The scaled method still misses the known
prediction by far more than the frozen tolerance. This gives no basis
for another native comparison of the centered method under the same
design. The existing trust-region method remains in use. A bounded method
that uses the full derivative geometry would need separate qualification.
The [direct and QR-reduced replay](QR_SOLVER_REPLAY_RESULT.md) later
passed all seven exact linear controls without revising these failures.

The run checked six saved 120-second derivatives and one 24-second
derivative, with all 2,786 evaluations recorded. Linear predictions are
reported in whitened units. No sensor records, protected data or native
propagation were used. The earlier native results retain their original
dispositions.

## Reproduce the result

With the closed `data/scaled-solver-replay-v1` study restored, run the
report command. It verifies task results and charges without re-solving.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.scaled_solver_replay report
```

[Frozen design](SCALED_SOLVER_REPLAY_PLAN.md) ·
[All 14 task results and fit hashes](scaled-solver-replay-result.json)
