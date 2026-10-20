# Qualify directional acceleration inside the native enclosure

The static force component passed all 24 source/domain controls. The new
propagation candidate changes only the source of acceleration-change bounds:
an immutable, source-bound directional acceleration interval replaces the
training-conditioned interval. The original dynamics, native predictions,
physical bounds and 27 physical plus 24 shared-error columns remain. Original
shared-error caps and acceleration remainder are preserved.

The directional interval uses exact force calibration and rotation inequalities,
with a declared 1e-10 m/s² numerical margin. Its physical-domain certificate must
match the complete source reference and domain. The candidate still carries the
original remainder; the new value range must not be treated as a Taylor error.
It uses no training observations or known calibration to construct its bounds.

Reuse all 24 original native qualification inputs and acceptance limits: center
and independent stationary-pose agreement within 1 micrometre; all 162 derivative
columns checked at step .002 within 20 micrometres per normalized coordinate;
all original nonlinear probes within the supplied remainder plus the existing
10 micrometre arithmetic margin. Every common-error column remains mandatory.
The new candidate and original engines are separately frozen.

Finite allowance: **24 identities, 78 native evaluations, 19,632 native packet
visits, 348 bounds, 348 directional certificates and 15,072 bound packet-steps**
(two passes per packet). Four workers use one numerical thread each. Each bound
retains its cooperative 60-second ceiling; the overall ceiling is 600 seconds.
No retries, extensions, process signals, original aircraft/ESA reads, observed
fits or optimizer starts. Reserve each native evaluation and bound before it
runs. Preserve all source/input/environment hashes, charges and failures.

A fully passing result permits a separately frozen complete prediction-method
comparison. It does not establish recording-scale usefulness, a whole-program
floating-execution enclosure or calibrated observation coverage.

[Static component](../ilvis0-directional-force-controls/README.md) ·
[Original native qualification](../ilvis0-transform-native-controls/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
