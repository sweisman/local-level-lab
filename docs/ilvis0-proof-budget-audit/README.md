# Where the prediction allowance widens

All six saved cases pass this arithmetic audit. In every axis, the position-reconstruction term accounts for more than **99.999% of the saved unshared allowance**; the other reported component is the mounting-offset term.

This comparison divides one allowance into its two saved components. It does not allocate every part of the final prediction range, measure aircraft error, or establish why that term became large. It identifies the position-reconstruction calculation as the next place to investigate.

The original six prediction ranges still fail their usefulness targets. V01 remains unqualified. No new integration, prediction bound, optimizer start or aircraft-data read was performed.

The audit verified the original completion, summary, case and certificate hashes, then checked that the two components reproduce each saved total. Its six identities used the shared study runner and indexed journal, with a 120-second limit and one thread; execution took less than one second.

[Method and limits](PLAN.md) · [Original completed comparison](../ilvis0-long-staged-feasibility-v2/README.md) · [Evaluator](../../analysis/lll/ilvis0_saved_budget_audit.py) · [Reproduce the evidence](../REPRODUCIBILITY.md).
