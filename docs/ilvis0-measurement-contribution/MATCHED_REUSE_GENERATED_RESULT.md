# Skipping repeated solver evaluations

The solver now has an option to reuse the result of a previously rejected
proposal when it encounters the exact same proposal at the same accepted
point. In eight generated aircraft fits, this reduced training evaluations
from 282 to 239, a 15% reduction. All eight comparisons met the criteria
set before the run. The seven fits that previously converged still converged.
The eighth still failed its stopping check. Final training costs and later
predicted positions matched the saved results in all eight cases.

The run recorded 56 uses of a previous rejection. Some reused proposals were
followed by other evaluations, so the net saving was 43 training evaluations.
The study charged 247 native calls, including eight calls for the forecasts.

The [recorded-aircraft follow-up](MATCHED_REUSE_OBSERVED_RESULT.md) also
reproduced two previously passing fits exactly. Neither contained a
duplicate rejection. The original incomplete IMU8 result stays in the
evidence record.

[Frozen plan](MATCHED_REUSE_GENERATED_PLAN.md) ·
[Per-fit results](matched-reuse-generated-result.json) ·
[Reproduction bundle](matched-reuse-generated-evidence/bundle.zip)
