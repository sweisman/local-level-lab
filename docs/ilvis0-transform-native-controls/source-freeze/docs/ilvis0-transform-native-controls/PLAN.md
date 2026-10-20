# Native common-transform qualification

The common matrix and common-clock components each pass their 24-control
qualification. A new native enclosure now extracts the shared matrix-weighted
raw-force integral algebraically, preserving the original dynamics and bounds.
The seven local native checks pass, including a varying radial-force/gain
control and all three model candidates under both processing cases.

Freeze the **same 24 generated inputs** as the completed common-acceleration
native qualification. Preserve every physical parameter and all original
centre, derivative, independent stationary-pose and probe-containment criteria.
The new enclosure retains 27 physical plus 24 auxiliary columns, 51 in total.
Known common errors must remain within their caps. No old study is relaunched.

Acceptance limits remain: centre/known-pose agreement within 1 micrometre;
all 162 finite-difference derivative columns within 20 micrometres per normalized
parameter at step .002; generated probe residuals within the supplied unshared
remainder plus the existing 10 micrometre arithmetic margin. No empirical
likelihood, error distribution or production eligibility is changed.

Finite allowance: 24 identities, 78 native evaluations, 19,632 packet visits,
348 bounds and 7,536 reserved bound steps. Four workers use one numerical
thread each. Allow 600 cooperative seconds overall and 60 per bound for the
new exact integral and matrix bookkeeping. A bound shares its own deadline
between integral construction and propagation. No retries, extensions,
process signals, original aircraft reads or observed fits.

Only a fully passing, verified result permits a separately qualified typed
51-column joint interface and complete prediction comparison. Full floating-
point execution, recording-scale usefulness and observation-error adequacy
remain separate requirements even if these generated controls pass.

[Native derivation](../ilvis0-common-force-transform/NATIVE_PLAN.md) ·
[Clock controls](../ilvis0-force-clock-controls/INTERPRETATION.md).
