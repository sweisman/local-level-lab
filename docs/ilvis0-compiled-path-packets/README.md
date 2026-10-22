# Faster packet-by-packet uncertainty calculation

The compiled adapter connects the checked motion step to the full input path:
initial position, velocity and orientation; sensor offsets and gains; gravity;
mounting offset; clock; and upstream field removal. It retains all 27 parameters.
Every earlier packet is integrated before the final partial packet.

Ten local checks pass. They compare the adapter with the independent rational
reference, check a nonzero common parameter range, verify clock and vertical
offset signs, and reject invalid inputs. Raw constants must already have exact
binary64 representations; unsupported conversions are rejected rather than
silently changing the supplied measurements. Buffers are copied before use.

The separate [64-packet comparison](../ilvis0-compiled-path-controls/INTERPRETATION.md)
passes all six cases and all 27 parameter directions in 57.44 seconds. It used
six native queries and 10,368 interval packet steps, with no aircraft fits.
Every native value and first derivative falls inside its computed interval.

These are software checks on supported branches. Useful ranges for complete
recordings, complete clock/rotation boundaries, native execution error and an
aircraft error model remain unqualified.

[Motion step](../ilvis0-path-step/README.md) ·
[Prediction requirements](../ilvis0-long-staged-feasibility-v2/V01_GATES.md)
