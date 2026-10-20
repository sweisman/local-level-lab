# Native cancellation required for the common force transform

This is a derivation and implementation gate, not a native qualification or
observed-data allowance. Preserve the existing enclosure and its frozen studies.

## State identity

Let \(S\) be the common accumulated clipped period, \(G,H\) the raw-force
integrals defined in [the clock plan](CLOCK_PLAN.md), and \(A\) the existing
common initial acceleration. Preserve the exact representation

\[
v=v_0+A S+M G+w.
\]

At a packet midpoint, let \(B=(I+[a]_\times)^{-1}\), and let
\(F_{\rm rel}=(Q R_0P-R_0)f_{\rm current}\). The existing acceleration-departure
update before extracting the raw-force contribution is

\[
\Delta u=B\{M\Delta G+\Delta t F_{\rm rel}
-2a\times v-\Delta t(a\times A)\}.
\]

Using \((B-I)x=-B(a\times x)\), subtract \(M\Delta G\) algebraically:

\[
\boxed{\Delta w=B\{\Delta t F_{\rm rel}-2a\times v
-\Delta t(a\times A)-a\times(M\Delta G)\}.}
\]

Do not compute a widened interval for \(\Delta u\) and subtract another
widened interval. The cancellation must occur in the equation itself.

Both the estimate and revised midpoint calls use this identity. Their midpoint
state must include \(A(S+\Delta t/2)\), \(M(G+\Delta G/2)\), and
\(w+\Delta w_{\rm estimate}/2\). Keep the same old-velocity term in the
implicit Coriolis equation as the original implementation.

## Position identity

For the fixed reference coordinate metric \(m_0\), separate the rate into

\[
\dot c=m_0(v_0+A S+M G)
+m(c)w+(m(c)-m_0)(v_0+A S+M G).
\]

Integrate the last two terms as departures. Accumulate raw integrals with
\(\Delta G=f_{\rm raw,diff}\Delta t\) and
\(\Delta H=(G+\Delta G/2)\Delta t\). Reconstruct position from
the initial position, \(m_0v_0S\), \(m_0 A S^2/2\), \(m_0MH\) and departures.
Preserve every geographic metric, transport, gravity and lever term.

Internal states retain complete bounds on \(MG\) and \(MH\), including their
common errors; these full bounds protect feedback into transport and metrics.
Only at the final additive output may the qualified clocked-transform remainder
replace the generic \(MH\) remainder and emit its nine shared coefficients.
Its total change/range must still include the full matrix error. Existing
velocity/time, initial-lever and common-acceleration blocks remain intact.

## Clock and typing

Use the actual clipped-packet clock. An internal prefix may finish before the
query interval; it must not be passed to an API requiring the whole query to
lie inside that prefix. Ordinary conservative prefix bounds are acceptable for
internal feedback. The tighter final common-clock integral uses the complete
unchanged input support and retains its tag-defect allowance.

A new 51-column enclosure must bind the raw inputs, original physical box,
expansion, acceleration reference, matrix reference and clock-integral report.
It must not masquerade as the older 42-column type. A later joint interface
checks all bindings and all columns and excludes future receiver observations.

## Required qualification

First qualify the exact integral and clocked-matrix components. Then freeze a
separate native candidate using the unchanged all-model/generated inputs and
original centre, derivative, known-pose and probe-containment limits. Compare
all 27 native derivative columns and retain all 24 auxiliary columns. Do not
run a full prediction comparison or aircraft fits after any failed gate.
Each study needs explicit finite work limits before launch; this derivation
spends no earlier allowance and creates no observed-data authorization.
