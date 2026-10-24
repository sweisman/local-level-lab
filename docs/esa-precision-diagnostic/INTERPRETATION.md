# What the precision comparison found

All 24 saved-point comparisons completed. At each original calibration and its
saved correction, the binary64 path reproduced the earlier residual vector
exactly. The run used 96 value calculations in 67 seconds and performed no fit.

For the eight specified-field globe points, the original calculation meets the
cost-change component at one point. Changing longitude wrapping alone raises
that to two points, but does not consistently remove the failures. With wider
precision during integration and coordinate subtraction, all eight cost changes
fall below the unchanged 1×10⁻⁸ limit. The largest is about 8.31×10⁻¹⁰.

The physical equations, binary64 packet scheduling, query fractions, parameter
products and processing-fraction mapping are held fixed. The result supports
precision sensitivity in the accumulated calculation. It does not supply a
certified roundoff bound or establish that these saved points are global optima.

No original fit is reclassified. The next gate qualifies a full wider-precision
residual-and-derivative path, together with the unchanged stopping checks, on
independent known-answer examples. Only then can a separately frozen study use
that method in a solver. Seven confirmation flight groups remain protected.

[Verified comparison](README.md) · [All points and modes](precision.csv) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
