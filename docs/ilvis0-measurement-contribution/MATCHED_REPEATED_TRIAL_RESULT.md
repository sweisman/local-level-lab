# Seven repeated full proposals used part of the IMU8 allowance

Seven of the 30 charged training evaluations in the stopped IMU8
zero-field disc fit repeated full proposals already rejected at the same
accepted point. The repeats were 10, 12, 14 and 16 from proposal 8, 20
and 22 from proposal 18, and 28 from proposal 26. Their recorded trial
costs, predicted decreases and step lengths reproduce exactly. The
other six sealed fits have no repeats of this type.

The opt-in solver check reuses only an exact rejected full proposal at
the same accepted point. It still runs the local trust-region step and
all fresh stopping checks. On the curved control it kept the same
endpoint, objective and stopping result with fewer evaluations, using
either the tangent or the value-only proposal calculation. Sixteen
additional curved, bounded and higher-dimensional controls reached their
known objectives and positions. The unfinished control still failed its
stopping check. All 68 focused tests passed.

The changed proposal rule has no observed-flight qualification yet.
The IMU8 failure remains in the original evidence. The completed IMU21
continuation used its archived original solver.
The [generated aircraft check](MATCHED_REUSE_GENERATED_RESULT.md) reproduced
the stopping outcomes, costs and forecasts of all eight saved reference
cases with 43 fewer training evaluations.

Verify the saved trace audit from the repository root.

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.ilvis0_repeated_trial_audit check
```

[Check design](MATCHED_REPEATED_TRIAL_PLAN.md) ·
[Saved trace audit](matched-repeated-trial-audit.json)
