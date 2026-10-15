# Why the first trust-region candidate failed qualification

The [original qualification tests](original-qualification.py) are retained as
historical evidence, with their exact failed-study source hash. They are separate
from the current regression matrix; the original four failures remain recorded.

The failed candidate missed the same known-answer control from all four starts.
The control has 27 parameters, an invertible monotone nonlinear transform and a
linear map with singular values from 10,000 to 0.0001. The known feasible optimum
has objective 1. Weak parameter directions make it a demanding numerical test;
it is not an archival flight or an Earth-model simulation campaign.

Four separately bounded diagnostic replays reproduced the failures. Every start
used 199 of its 200 allowed evaluations and stopped without passing stationarity.
Final objectives ranged from 1.00005157 to 1.00076924. The solver was still accepting
small corrections, with late normalized step lengths around 0.0037–0.0121.
Its damping and trust radius could remain unchanged when actual improvement was
between one quarter and three quarters of the local prediction. Progress along
weak directions was therefore repeatedly restricted. The preserved
[replay measurements](diagnosis.json) include every history and endpoint.

Removing routine damping improved an initial prototype from 44/48 to 46/48,
but two starts still exhausted their allowance. A short box-constrained correction
can point in a different direction from the full correction in a curved, poorly
conditioned valley. That prototype and its failed screen remain preserved.

The final revised candidate first tests the full feasible bounded Gauss–Newton
correction. Only a rejected full correction invokes the smaller trust-region
proposal; damping is a fallback for an unfinished local solve. Every evaluated
proposal is counted. This retains the established full-step path where it works
and supplies a different bounded direction when it does not.

The separately frozen [revised qualification](../ilvis0-trust-v2-qualification-20261015/RESULTS.md)
passed all 48 original checks, including six independently constructed raw-increment
motion controls and two negative controls. Physical models, parameter bounds and
the final **undamped** stationarity, cost and actual-position checks are unchanged.
Small trust-region steps cannot establish convergence by themselves.

This explains the observed software-control failure; it does not establish that
the same mechanism caused every unfinished archival fit. The separate
[matched archival trial](../ilvis0-trust-trial-20261015/README.md) tests that transfer.
