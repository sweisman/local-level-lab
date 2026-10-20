# Geographic propagation and receiver-position bounds

All **72 generated controls passed**. This closes the single-packet geographic
predictor/corrector and antenna-position calculation around the unchanged native
integration code. It adds no aircraft-data fits or new scientific detections.

The calculation preserves all 27 calibration, initialization, lever-arm and
timing directions. Cases cover both hemispheres, all three physical candidates,
narrow and broad calibration regions, and processing fractions centered at
either physical boundary. Timing is fixed at a packet endpoint or varies
strictly inside a packet. Continuous longitude is preserved.

There are 4,608 declared probes. Values are checked against the original C
kernel; all parameter derivatives are checked against the original C++ tangent
and independent complex-step calculations. The largest derivative discrepancy
is below 2.85e-14 metres per normalized parameter. The analytic remainder bounds
cover their declared regions; sampled discrepancies are checks, not the source
of those bounds. Comparisons below the stated arithmetic tolerance are recorded
separately, rather than presented as precision measurements.

The study used 4,680 C calls, 72 C++ calls and 6,624 independent references in
13.94 seconds. All 246 publication artifacts pass their SHA-256 checks. The
[frozen plan](PLAN.md) and [result tables](README.md) preserve the exact scope.

## What remains

A short-step bound need not remain useful after thousands of repeated steps.
The next component must propagate complete histories and handle receiver-time
uncertainty crossing packet boundaries. Whole-record arithmetic and shared
receiver-error assessment also remain open. These checks precede a new withheld
prediction study; earlier aircraft findings and failed studies are unchanged.

[Next component](NEXT_PLAN.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
