# Preserve coordinate bounds through the native calculation

Build a separate native-enclosure candidate that carries both an overall
vector-norm bound and separate coordinate bounds through addition, scaling,
cross products, matrix actions, velocity updates and coordinate extraction.
Retain the tighter applicable bound at each operation without converting one
norm radius into three independent equal coordinate uncertainties.

Preserve the native equations, centers, physical assumptions, all 27 physical
and 24 shared columns, calibration remainder and previously verified training
conditioning. Physical-domain force proofs may be used by generated native
controls; the prediction path must retain its training-derived certificate.
Never replace the latter with a weaker physical-only range.

This stage qualifies transport of component bounds. It does not yet install the
new norm-constrained body-source interval into the full engine or authorize a
complete prediction rerun. That source integration remains a separate gate.

Keep the original 24-case native control matrix and numerical limits: center
and stationary-pose agreement within 1 micrometre, 162 finite-difference columns
at step .002 within 20 micrometres per normalized coordinate, and all nonlinear
probes within the computed remainder plus 10 micrometres arithmetic margin.

Finite study allowance: 24 identities, 78 full native evaluations, 19,632 native
packet visits, 348 bounds, 348 physical source certificates and 15,072 bound
packet-steps (two passes per packet). Four single-thread workers; each bound
has a cooperative 60-second ceiling and the study a 600-second ceiling.
Freeze sources, inputs, compiler and environment before launch. No retries,
extensions, observed fits, original-aircraft reads or protected ESA data.

Passing these controls qualifies this implementation component, not aircraft
prediction coverage or statistical significance. Preserve every earlier freeze.
