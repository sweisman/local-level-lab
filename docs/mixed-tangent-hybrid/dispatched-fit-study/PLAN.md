# Model-declared tangent: generated fit qualification

## Question

Does choosing the tangent from the declared physical model before fitting preserve the existing wide-precision fit and forecast on complete generated cases?

## Fixed design

Use the completed short paired-fit recipe: six 120-second generated cases, covering three physical models and two processing settings at 55° latitude. Within each case the measurements, optimizer, bounds, start, training split, withheld truth and 119 queried receiver epochs (40 held out after training) are identical. The reference always uses the wide tangent. The candidate uses the first selective tangent for either globe model and the wide tangent for the flat model. Outcomes never determine the choice.

Each pair has at most 402 native calls; the six-case ceiling is 2,412 calls and 4,517,436,000 packet/query visits. Use four workers with one numerical thread each, a two-hour wall ceiling and no observed or protected recording. Charge before work. Save inputs, source and environment hashes, kernel binaries, both fits, forecasts, failures and task journals. The source-bound qualification must include the task-resume reboot test. If a technical interruption occurs, keep every sealed success and failure; a separate unchanged-input continuation may permit at most two starts per unfinished task, six technical interruptions across the study, and two hours of additional wall time. No completed task may restart. Prepare a new source-bound study identity and finite allowance. Do not modify either earlier paired-fit study.

Pass only if both fits independently converge, retain all nuisance columns, meet the existing physical prediction screen, and differ by at most 0.01 m at every forecast epoch. Report every result even if the gate fails. This is generated software qualification. Observed-aircraft substitution remains separately gated, and the established wide method stays in use.
