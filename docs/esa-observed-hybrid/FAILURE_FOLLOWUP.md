# Why the faster ESA tangent method remains unqualified

The [verified same-source comparison](combined/README.md) passed 21 of 24
paired cases. Its fixed rule required every pair to pass, forecasts to agree
within 0.01 m and both methods to choose the same training-cost primary start.
That rule failed and has not been changed.

The three differing primary choices are near ties in training cost. A
[saved-only comparison](PRIMARY_DIAGNOSTIC.md) finds that changing between the
chosen starts changes their forecasts by at most 0.000079 m. Those start flips
are a reproducibility issue for the exact selection rule, but they do not
explain the pair with a 0.016715 m method difference.

For that pair, the discrepancy grows across the 1,200 saved forecast epochs.
Its median is 0.000840 m, its 95th percentile is 0.013332 m, and its maximum
is at the final epoch. The maximum components are about −0.011728 m north,
+0.005884 m east and +0.010355 m up. This is a numerical comparison between
two fitted calculations on one prepared ESA recording, not a physical
measurement discrepancy.

The [reproducible saved-fit comparison](FAILURE_DIAGNOSTIC.md) confirms this
pattern for all three failed pairs. The 0.016715 m case differs most in its
normalized `position_x` parameter by 0.00001316, despite nearly identical
training costs and the same active bounds. Another failed pair has forecasts
that differ by only 0.00000373 m; its failure is numerical qualification, not
forecast disagreement. These differences do not yet isolate a derivative
column: the two methods must be compared at an identical saved parameter point.

The other two failed pairs use the short receiver-error policy and the flat
model. Their fit records terminate as unresolved after a “no positive
predicted decrease” message, at 88–90 evaluations below the 200-evaluation
ceiling. One wide fit passes while its faster counterpart does not; in the
other pair neither fit passes. A larger evaluation ceiling alone is not a
supported explanation.

The next method-development step is to compare the two tangent calculations
at the saved failed parameter points, by active column and over time. Any
precision change or revised near-tie selection rule needs a **new** source
freeze, fixed numerical allowance and complete paired comparison. The
existing 0.01 m limit and the failed 24-case result remain intact. Until a
separate method qualifies, the established wide calculation stays in use.

The shared same-point column comparison
now passes two deterministic software checks. It expresses each derivative
difference as metres of north/east/up position per normalized parameter and
records the largest epoch and column. Applying it to the sealed ESA points
still requires a separately frozen finite diagnostic; this software check
does not requalify the faster method.

## Finite saved-point diagnostic to prepare

Use exactly the three failed identities in the [verified paired report](combined/README.md).
For each identity, take both sealed fitted parameter points. Evaluate the
established and faster tangent once at each identical point, using the same
800 earlier receiver epochs and the 239,867-packet inertial prefix. This is
four native calls per identity, twelve total, with no optimizer starts and no
later receiver positions. The maximum is 767,574,400 packet/epoch visits per
identity and 2,302,723,200 in total. Keep one numerical thread per worker and
at most three workers. Charge each call before execution and preserve an
interrupted task's charge. Freeze the exact source, environment, prepared-input
hashes, saved-fit hashes, task list, thread allocation and cooperative wall
limit before launch; qualify task-level recovery first.

Compare value identity, boundary counts and every active derivative column in
local position units, including the largest difference and its epoch. Report
the measured differences without choosing a new tolerance from this data.
The original 24-pair gate and all its failures remain unchanged. Any revised
method or selection rule requires a separate complete qualification study.

The first three-task diagnostic allowance closed with three direct-loader
import failures before any native call (0/12 charged). Its terminal result is
preserved. A new direct-file loading test now covers the corrected adapter;
the prepared receiver-time binding and no-fit training setup were also checked
against the frozen development inputs. The corrected diagnostic requires a
fresh source-bound allowance and keeps the same twelve-call ceiling.
