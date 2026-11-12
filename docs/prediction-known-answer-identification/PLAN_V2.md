# Known-answer identification: corrected result schema

The first frozen four-task study completed its 404/404 charged operations and
1,624/1,624 charged numerical steps. All four results were sealed as failures
because its adapter omitted the runner-required `scientific_decision="abstain"`
field. No numerical result from that allowance is promoted, and it is not
restarted. Its saved failures and source freeze remain part of the audit trail.

This second finite study preserves the exact same synthetic generator,
candidate laws, seeds, training/withheld split, thresholds, scientific scope,
one-thread allocation and per-task limits in [the original plan](PLAN.md).
Its sole code change wraps the original evaluator and explicitly declares
scientific abstention in the result schema. It gets a new source/environment
freeze, software qualification, task-level recovery check and separate
404-operation allowance. The preparation requires the first study's exact
terminal failure and charges, so the correction cannot erase that history.
