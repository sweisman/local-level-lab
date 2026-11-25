# How a future decision would count flights

The planned confirmation test counts one result per frozen flight group.
Overlapping stretches, different views of the same flight and closely related
recordings stay together. Each group supplies one calibrated test against each
candidate and a separate check of whether each candidate predicts the
observations well enough. Technical failures, abstentions and missing results
stay in the total.

The checked software requires a specified number of groups to meet the same
criterion. A disc decision requires evidence against both globe variants
within the same groups. A globe decision requires evidence against the disc
and adequate globe predictions. Only after a globe decision can the test
compare background fields. A field decision also requires the same groups
to rule out the disc and the other globe variant. Conflicting directions
lead to abstention.

## What the statistical rule controls

Let (G) be the total number of frozen groups and (r) the required number
showing the specified contrast. Use the (r)-th smallest group p-value
multiplied by (G-r+1), capped at one. Under the hypothesis that fewer than
(r) groups genuinely show the contrast, at least (G-r+1) groups have valid
null p-values. If the (r)-th smallest crosses the group threshold, at least
one of those null groups must cross it. The union bound controls the chance
of that event without requiring independence across groups.

For a common true candidate in the specified model set, a wrong shape or a
wrong field decision both require rejecting that candidate in at least (r)
groups. The two stages use the same cohort, minimum group count and threshold.
This controls the combined error event if the group tests are valid for that
candidate. Requiring physical adequacy can only reduce support. It cannot
make a competing candidate easier to reject.

For illustration, with seven groups and a 5% error allowance, these thresholds
would apply to the (r)-th smallest group p-value. The confirmation policy
still needs to specify its own (r) and error allowance in advance.

| Required groups | Group p-value threshold |
|---:|---:|
| 1 | 0.00714 |
| 3 | 0.01000 |
| 5 | 0.01667 |
| 7 | 0.05000 |

## What has been verified

Known-answer checks cover incomplete groups, contradictory evidence,
adequacy vetoes and the need for multiple comparisons to agree within a
group. An exact 1,000-case dependent control reaches the 5% bound in 50
cases. This checks aggregation given valid inputs. The per-group aircraft
tests still need to account for fit uncertainty, the receiver error law,
and any choices within each group. The [forecast coverage question](PREDICTION_GROUP_COUNT.md)
is separate. The seven groups remain reserved.

The seven ESA groups use the same identified iMAR unit as the development
flight. The group rule allows dependence between valid group tests. The
error model still needs to cover persistent sensor and installation effects
within each group's calibration. [Instrument provenance](external-imu-data/ESA_INSTRUMENT_PROVENANCE.md)

A [reference-sample audit](prediction-observed-development/GROUP_RANK_RESOLUTION_RESULT.md)
shows why the existing twelve generated histories are too few for these
within-group tests. A future design needs both sufficient rank resolution
and an error law that applies to the target aircraft.

The [matched forecast score](PREDICTION_GROUP_DECISION.md) now connects
saved candidate errors to this rule. It preserves the frozen reference
denominator even when a draw is missing and keeps forecasts that fail the
adequacy check from supplying support.

## When additional reference draws cannot change a rejection

A [work bound](../analysis/lll/group_rank_work.py) tracks two ranks for each
declared error scenario while its fixed list of reference draws is still
running. The best possible rank treats every unfinished draw as less
extreme than the target. The conservative rank counts every unfinished
draw as extreme. Both count sealed failures and ties as extreme. Use the
largest rank across scenarios for each bound.

If both bounds give the same rejection outcome at the frozen cutoff,
additional draws cannot change that outcome. A draw can be left unused
only if no other planned check needs it. The cutoff and the original
denominator stay fixed. Report the conservative rank as the p-value
and record the bounds and unused draw IDs. The best possible rank serves
only to decide whether more computation is needed.

For example, with a cutoff of 0.01 and 199 planned draws in a scenario,
two sealed ties or failures are enough to rule out rejection immediately.
At the other end, 198 sealed draws less extreme than the target are enough
to reject even if the last draw is unavailable. With just 99 planned
draws, rejection requires every draw to be scored and less extreme.

The [exhaustive software checks](../analysis/tests/test_group_rank_work.py)
compare both bounds with all completions of small reference sets, including
ties and failures. A zero target fixes the rank probability at one before
any reference run because all reference scores are nonnegative. This can
remove an unnecessary calculation when a candidate ties or wins in even
one matched setting. A shared reference draw may still be needed for a
different target. The check used no aircraft data. A future study still
needs a qualified error law and exchangeable reference draws.

### When the whole cohort can stop

Once all target scores and accuracy checks are final, the
[cohort work check](../analysis/lll/group_cohort_work.py) traces the votes each
flight group could still contribute. It applies the same shape-first decision
rule to every attainable combination of vote counts. This keeps the links
between the votes from each group. For example, a group can support a field
only if it also supports globe geometry.
When groups share a reference result, their ranks can move together. The check
allows them to move separately, which can leave extra outcomes possible.

If just one shape-and-field outcome remains possible, unfinished draws cannot
change the cohort's decision. A frozen study can then leave those draws unused
if no other required check needs them. The report still counts all unfinished
draws in the upper tail. Shared draws can be counted in more than one rank, so
the number of pending slots can exceed the number of calculations left.

The [software checks](../analysis/tests/test_group_cohort_work.py) match the
possible outcomes against exhaustive completions. They also cover a case in
which two groups fix both decisions while 237 slots in a third remain pending.
This verifies the calculation. It gives no estimate of work savings or
statistical coverage on aircraft.

### When all queries share the same reference draws

The matched-score pipeline can use `compare_shared_cohort_work` once all
target scores and adequacy checks are final. A reference score that
counts against a higher target also counts against every lower target for
the same candidate. The possible rejections therefore fall at a single
cut in the score order, and tied targets stay together. One cutoff still
works across multiple error scenarios because the target score order is
the same in every scenario.

The check tests each possible cut using the two targets on its boundary.
A cut is attainable if pending reference scores placed between those
targets can retain the lower target and reject the higher one. It then
applies the unchanged shape-first rule to those votes. The reported
conservative decision still counts unfinished draws in the upper tail.

In a three-group software check, two targets shared the same disc score
and supported opposite field conclusions. The common draw could make
both groups pass or neither pass. A third group already fixed the shape
as globe. The shared-reference check fixed the field at abstention with
one draw pending, while the separate-rank check could not close the case.
This checks work planning. Aircraft error calibration is still required.

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 --reserved-threads 0 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_group_cohort_work.py analysis/tests/test_group_rank_work.py \
  analysis/tests/test_flight_group_decision.py analysis/tests/test_group_rank_calibration.py \
  analysis/tests/test_prediction_group_decision.py
```

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m pytest -q \
  analysis/tests/test_flight_group_decision.py analysis/tests/test_group_rank_calibration.py \
  analysis/tests/test_group_rank_work.py
```

[Frozen group provenance](PROVENANCE_VERIFICATION.md)
