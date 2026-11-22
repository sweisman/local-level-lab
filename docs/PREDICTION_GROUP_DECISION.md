# From matched forecast errors to a flight-group score

One prespecified group of related recordings contributes one comparison. This
development rule takes saved prediction errors and a separate physical adequacy
check for each of the three candidates under every frozen setting. A group
with an incomplete comparison abstains. This rule has no access to recordings
or model fitting.

For each candidate and setting, subtract the error of the best of the three
candidates from its error. Use the smallest of these gaps across the settings
as the group's score against that candidate. A candidate that ties or wins
even one setting has score zero. Fix the group composition, setting list,
error measure, adequacy checks and calibration population before use.

The module sends the score to the existing
[rank calibration](../analysis/lll/group_rank_calibration.py). Its inputs
declare all reference IDs separately for every candidate and error scenario.
Ties and missing references stay in the upper tail. The largest rank
probability among scenarios protects against rejecting a candidate just because
one assumed error scenario makes it look implausible.

The resulting rank probabilities and adequacy flags feed the existing
[flight-group decision rule](FLIGHT_GROUP_DECISION.md). A globe call needs
evidence against the disc and an adequate globe alternative. A disc call
needs evidence against both globe candidates and an adequate disc. The field
result opens only after a globe call. Adequacy can withhold a decision and
cannot exclude a candidate. The module also shows a single-group decision for
checking the wiring. Every output retains scientific abstention.

If one of the specified candidates generated the flight and its group score is
exchangeable with its calibration scores, the chance of excluding that true
candidate is at most the prespecified allowance. Either a wrong shape decision
or a wrong field decision would require that exclusion. The same statement
covers both stages for one group, even though the field stage is opened by the
shape stage. It supplies no coverage guarantee for a mixture outside the
specified hypotheses or a collection of selectively reported groups.

## A cheaper reference test

The optional `absolute_null=True` mode fits only the known generating
model for each reference draw. A query flight still needs scores from all
three candidates in every setting. The reference score is the generating
model's smallest forecast loss across settings. The query score is its
smallest gap to the best candidate across the same settings.

All losses are nonnegative, so the query gap is at most the query's own
loss. Comparing the gap with reference own losses therefore gives a rank
probability at least as large as ranking the query's own loss. The usual
finite-sample guarantee follows if the candidate's own losses are
exchangeable within the relevant error scenario. Unavailable references
count in the upper tail and incomplete queries abstain. The protocol must
bind the reference method, loss, receiver target, fit procedure, settings
and population. The single-model reference fit must produce the same own
loss it would produce within the matched fit. Shared fitting information
from other candidates could break that requirement.

This uses one model fit per reference setting instead of three. It may be
harder to rule out candidates because the absolute reference losses
include errors all three models share. The checks rotate each of five
reference histories into the query role for each possible generating
model. They also verify ties, missing scores and the minimum across
settings. This is a software check with constructed scores.

The [4,344 saved simulation fits](prediction-validation-continuation/README.md)
span 181 draws and compare forecasts with known simulated positions.
They do not have matched receiver-target losses for this test and were
reserved for validation of their original rule. A future study needs a
frozen aircraft error model and separate reference and validation draws.

## Software checks

The [known-answer checks](../analysis/tests/test_prediction_group_decision.py)
cover both shape outcomes, field abstention, inadequate forecasts, ties,
incomplete groups, a missing reference scenario and mismatched identities.
Across all five query assignments for each true candidate, the single
assignment that excluded truth was also the only one that gave a wrong
shape or field decision. The settings within each group were linked.

The checker also reads the [sealed 12-recording generated result](prediction-observed-development/MATCHED_CANDIDATE_GENERATED_RESULT.md).
With each recording held out in turn, the most favorable illustrative pool
had three references under its true model and four under each other model.
At a 5% allowance all 12 checks abstained under both reference methods
because the rank could never be small enough. The recordings differ in
route and noise law. This pooled replay exercises the input format and
supplies no decision calibration.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -q analysis/tests/test_prediction_group_decision.py
```

Even in the most favorable case, a single-group 5% test needs at least 19
available references per declared scenario. Larger cohort requirements follow
the [reference count calculation](prediction-observed-development/GROUP_RANK_RESOLUTION_RESULT.md).
As a separate planning example, demonstrating a failure rate below 5% with
simultaneous 95% confidence in three validation populations and zero failures
would require at least 80 independent validation groups in each population.
That is the smallest count for which `tail_upper(n, 0, 3, .95) < .05`.
These examples address rank resolution and false decisions. Power and
relevance to aircraft also require a justified generating population.

Both versions require a separate frozen calibration for each candidate and
an independent test of the entire procedure on a justified population. Keep
the seven reserved ESA groups closed until the prerequisites are satisfied.

For a future matched-reference run, `compare_group_work` uses those scores and
adequacy flags to produce rank bounds from the sealed reference results. Pass
those rows and all final unavailable group statuses to `cohort_rank_work` with
the same cohort, required group count and allowance. The
[cohort work rule](FLIGHT_GROUP_DECISION.md#when-the-whole-cohort-can-stop)
checks whether either decision could still change. Missing calibration results
and sealed failed draws remain distinct for this calculation.
