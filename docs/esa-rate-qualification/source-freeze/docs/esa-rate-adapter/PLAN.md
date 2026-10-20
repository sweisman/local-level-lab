# ESA engineering-rate integration controls

ESA's iMAR records contain angular rates and accelerations in engineering units,
not Applanix integer increments. This prerequisite constructs clearly labeled
candidate increments from adjacent records while retaining both original rows.
It does not determine which sampling/averaging convention the instrument used.

Add a streaming adapter in `analysis/lll/airquantumgrav_increments.py` supporting
three explicit hypotheses: rate held from the left endpoint, rate held backward
from the right endpoint, and linear point-rate quadrature. Use actual timestamp
differences. Keep interval support and any explicitly supplied alignment offset
separate from the original time tags. No bias, mounting, gravity or background
rotation correction is allowed. Reject malformed rows, reversals and gaps;
never fill missing samples or give the first record fictitious preceding support.

Qualify constant, linear and sinusoidal generated channels against independently
integrated analytic functions. Compare declared derivative-bound quadrature
allowances with exact integrals. Test single-record, cross-chunk continuation,
unsupported gaps, alignment labels and preservation of original values.

Any error allowance is conditional on independently supplied derivative bounds;
it cannot be inferred reliably just by differencing adjacent noisy rates.
Integrating rate components is not the same as qualifying finite rotations or
coning/sculling. A full native rate-observation adapter still needs those tests.

This step reads no original ESA recording, performs no model fits, changes no
eligibility rule and inspects no protected flight. The finite qualification has
48 identities: 36 analytic quadrature cases (three hypotheses, three channel
families, four timestamp profiles) and 12 changing-axis/force body cases.
The limits are 1,152 component-interval evaluations, 24 ODE solves and 24,000
ODE right-hand-side evaluations, four total numerical threads and 60 cooperative
wall seconds. Each identity reserves its full finite allowance before execution;
there are no retries. Sources, environment and task identities freeze first.

Body comparisons use 1e-11 as an explicit numerical-reference allowance, with
two integration resolutions agreeing within that allowance. The bound remains
the declared mathematical bound; this allowance is not instrument uncertainty.
