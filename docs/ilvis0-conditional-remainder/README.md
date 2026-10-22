# A tighter bound on one force-error term

The first long-record cases retained a force Taylor-remainder bound of about
53.2 m/s², even after earlier observations constrained the total force change.
A checked algebraic bound can reduce that term while keeping the full linear
response in the calculation.

| Saved first-pair case | Original remainder bound | New conditional bound |
|---|---:|---:|
| Zero removal | 53.1557 m/s² | 6.1305 m/s² |
| Profiled removal | 53.1557 m/s² | 6.1563 m/s² |

**Nine new mathematical checks and 47 related checks pass.** Twelve exact
support checks revalidate the two saved force-change certificates. This work
performs no new native integration or fitting.

The original calibration box, reference, derivatives and shared coefficients
remain unchanged. The tighter bound applies only where its source force-change
constraint holds. It is not a new instrument specification or a measurement
of aircraft error.

The [native comparison](../ilvis0-remainder-native-controls/README.md) now passes
all twelve fixed controls, preserving shared coefficients and every known
probe. That qualifies this short component, not useful long-record prediction
ranges. The running long-record study and its failures remain unchanged.

## Why the linear term must remain

Write the change in force as a linear part plus a remainder:

\[
f(x)-f(x_0)=J(x-x_0)+r(x).
\]

If the total change on axis \(i\) is bounded by \(D_i\), then

\[
|r_i(x)|\leq D_i+\max_{x\in\text{box}}|[J(x-x_0)]_i|.
\]

The linear expression is bounded exactly over the original physical box.
Its interval and the supplied force-change interval give a remainder interval;
intersect that interval with the original remainder bound and round outward.
Small total change alone is insufficient: the linear term and remainder can
cancel. A dedicated check exercises that case.

[Source](../../analysis/lll/ilvis0_conditional_remainder.py) ·
[Checks](../../analysis/tests/test_ilvis0_conditional_remainder.py) ·
[Next native comparison](NATIVE_PLAN.md) ·
[First-pair diagnosis](../ilvis0-long-staged-feasibility-v2/FIRST_PAIR.md)
