# Remaining horizontal paired-cost continuation

The completed ridge-probe study passed all eight staged fits and five of six
paired comparisons. The only failure is zero-field globe / unsubtracted
increments: its costs differ by 1.67e-8, above the unchanged 1e-8 repeat limit.
The zero-start continuation exhausted 200 calls while reducing its cost.

Continue **both exact saved endpoints**, using the same algorithm, generated
observations, horizontal covariance, full nuisance columns and physical bounds.
No new method, probe radius, objective or acceptance threshold is introduced.

- Two new continuation identities, each with at most **600 tangent calls** and
  two diagnostic predictions: **1,204 native calls maximum**.
- Four numerical threads, fifteen minutes after compilation, no retries.
- No original-recording reads or observed-data fits. Earlier allowances remain
  closed; interrupted starts stay charged and cannot restart.
- Freeze parent completion, summary, public receipts, exact vectors, source,
  environment and this allowance before launch. Use exclusive locks, durable
  pre-call journals and atomic hashed outputs.

Both individual fits and their paired comparison must pass. Reuse only the ten
unchanged passing primary companions and the two saved fresh controls from the
preceding study; check all six pairs. Preserve the failed preceding review.
If this pair still fails, diagnose its solver trajectory before further fitting;
this plan authorizes no additional allowance or observed-data rollout.
