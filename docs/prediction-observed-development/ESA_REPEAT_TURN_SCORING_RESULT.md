# The repeat-turn scoring calculation passes its software checks

The scorer accepts a later receiver path only after verifying the
forecast seal and matching every timestamp. The seal covers the earlier
training identity, forecast values, native covariance and measured
angular exposure. The later receiver positions enter only through the
scoring interface.

The four covariance choices use the same sealed path. The native scales
come from the earlier 200/120 development forecast. Separate 0.001 m/s²
working terms test steady acceleration and a 15-second maneuver response,
alone and together. Neither term is estimated from the later positions.
The same covariance rule applies to opposite turns because it allows
horizontal errors in either direction.

All four source-bound checks passed. The implementation agreed with an
independent dense Gaussian calculation. It rejected tampered bytes and
changed timestamps, and preserved the covariance when a generated turn
was reversed. In 4,096 generated position-error draws, the combined
term met the declared joint reference check near 95% and had the best
mean log score among the tested choices. The simulation generated errors
from that covariance deliberately. Aircraft coverage, numerical fit
completion and the training-only forecast workflow still need to be
verified on their own terms.

The next execution step is to bind a fixed forecast method to the four
input receipts, qualify task-level interruption recovery and predeclare
its finite start and evaluation allowances. Later receiver positions
remain sealed until verified forecast outputs are available.

[Plan and reproduction](ESA_REPEAT_TURN_SCORING_PLAN.md) ·
[Source-bound qualification](esa-repeat-turn-scoring-qualification.json) ·
[Test report](esa-repeat-turn-scoring-tests.xml)
