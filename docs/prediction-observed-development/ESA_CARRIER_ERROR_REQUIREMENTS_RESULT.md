# How accurate the ESA measurements would need to be

With the full satellite set, the modeled errors cannot close the score
gap if independent measurements keep ground-covered range error below
about **2.10 mm RMS** and the other example caps hold. Those caps are
1 m per coordinate at each anchor, 1.876 mm/s² RMS trajectory error
acceleration and 2 mm RMS range error outside the ground receiver's
coverage.

| Satellite set | Maximum share at the example caps | Ground-covered range threshold with other caps fixed | Factor by which all example caps can change together |
| --- | ---: | ---: | ---: |
| Full set | 50.14% | 2.097 mm RMS | 1.978 |
| 0° starting tilt screen | 99.25% | 1.027 mm RMS | 1.007 |
| 5° starting tilt screen | 101.08% | 0.961 mm RMS | 0.989 |
| 10° starting tilt screen | 109.79% | 0.591 mm RMS | 0.911 |

These thresholds come from one fixed score bound on the development
flight. A factor below one means the example caps would need to tighten
together for that bound to exclude a full trajectory-error explanation.
A bound above 100% leaves the explanation open. It supplies no example
of an error that actually closes the gap.

Applying the geometric remainder separately to each range term also
tightened the upper bound for the 0° screen from 100.6% to 99.25%.
That leaves less than one percentage point of margin under the example
caps. The aircraft's antenna response and the actual errors shared by
its receivers still need independent checks. The agreement with the
ground receiver does not measure all of those errors.

All four previous bounds reproduced from the saved multipliers.
One task completed 245 charged checks with zero optimizer iterations,
new model fits or reserved-flight reads. Sixteen focused tests passed.

[Frozen plan](ESA_CARRIER_ERROR_REQUIREMENTS_PLAN.md) ·
[All one-at-a-time limits, coefficients and completion receipt](esa-carrier-error-requirements-result.json)
