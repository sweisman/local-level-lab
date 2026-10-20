# Geographic predictor/corrector and observation bounds

This extends the completed local-step controls through the actual native
geographic update and antenna observation. It uses generated inputs only.
Previous studies and kernels remain unchanged.

## Bound construction

Carry scalar intervals separately from nominal-value/change/remainder bounds.
This preserves asymmetric physical domains, including removal [0,1] centered
at either endpoint and a positive period whose symmetric outer ball crosses
zero. Intersect valid mathematical enclosures without clipping measurements.

Implement scalar product, inverse, sine/cosine and positive-domain powers with
global derivative/remainder bounds over their declared intervals. Keep latitude,
longitude and height in separate radian/metre components. Preserve continuous
longitude. Reject polar or metric-denominator crossings rather than repair them.

Mirror the native step exactly: old coordinate rates; midpoint coordinates;
first context using old rates; first local velocity estimate; revised rates at
the same midpoint using average velocity; revised context; second local step
from the original state; coordinate update using revised rates. Then rotate
the lever arm and map it with the candidate metric at the predicted position.

Allow a declared period within one packet and scale corrected full-packet
increments by that same fraction. Retain period/calibration cross terms.
Physical Coriolis and upstream removal remain distinct. This does not cover
a receiver-time interval crossing into another packet.

## Independent qualification

Use one unchanged C-kernel wrapper for full state and antenna values. Compile
the unchanged C++ tangent source separately and compare all 27 normalized
parameter columns with independent complex-step derivatives. A separate
reference uses matrix exponentials, linear solves and geographic formulas;
it does not call the bound implementation or repository step.

Seventy-two fixed cases: three candidates, latitudes ±65°, fixed removal or
profiled removal centered at zero/one, narrow/broad calibration, and fixed-
endpoint/interior timing. Each uses 64 predeclared probes in the complete
normalized box. Other parameter centers are nonzero. Interior timing spans
fractions [0.3,0.7] and is centered at one endpoint of that interval; endpoint
timing is fixed. Keep the timing column in every case and report when fixed.
Longitude cases cross the conventional ±180° display boundary without wrapping.

All parameter limits, sources, compiler configuration/binaries and numerical
environment are frozen before execution. Compare native observations and
coordinates in a fixed metre scaling at the seed location. Limits are 2e-8 m
for value discrepancies, 2e-10 m/s for velocity, 2e-12 for rotation and 1e-6 m
per normalized parameter for derivative discrepancies. Compare global Taylor
remainders with their analytic bounds plus those numerical tolerances and
`2e-12*norm(linear_term)`. Report roundoff-limited checks separately when a
remainder bound is smaller than the comparison tolerance. These tolerances
are not formal long-record rounding certificates.

Limits: 72 identities, 4,608 probes, 4,680 C step calls, 72 C++ tangent calls,
6,624 independent reference calls, 300 cooperative seconds, one worker/four
threads. Zero original reads, archive-native sweeps, optimizer starts or retries.
Reserve the complete per-identity allowance before execution; preserve failures
and never refund interrupted charges. No signals or process termination.

## Remaining scope

Short-step success does not establish useful bounds over a complete recording.
Repeated-step support, timing across packet boundaries, numerical enclosure and
shared observational covariance still precede a new archive prediction study.
No protected ESA observations or existing Earth-model fits are evaluated.

[Local-step controls](../ilvis0-local-step-bounds/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
