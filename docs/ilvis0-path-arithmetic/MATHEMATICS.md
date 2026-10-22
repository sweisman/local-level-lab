# Outward third-order operations

`ilvis0_path_arithmetic.cpp` reuses the unchanged numerical-mode checks and
interval primitives in `ilvis0_compiled_bounds.cpp`. Runtime arithmetic must use
binary64 round-to-nearest with gradual underflow; flush-to-zero and incompatible
rounding modes are rejected. Compilation disables fast-math and contraction.

Each elementary sum, product and quotient encloses its real result using
outward adjacent endpoints. Safe exact identities preserve zeros and units.
Underflowing products keep a positive upper allowance rather than disappearing.
Nonfinite or unsupported outputs fail.

Products use the binomial Leibniz rule for actual derivatives of orders 0–3.
Reciprocals and square-root derivatives use the same implicit recurrences as
the independent rational reference. A denominator containing zero is rejected.

For a positive square root, an exact power-of-two normalization puts the input
in [1,4). The library square root supplies a guess. Outward products independently
check whether each candidate endpoint squares below or above the normalized
input; at most eight adjustments are allowed before failure. Scaling the
certified endpoints back is exact because all finite positive binary64 inputs
have normal-range square roots. This avoids trusting an unchecked library
approximation or underflowing square comparison.

Sine and cosine values use the same degree-40 Taylor specification and
`|x|^41/41!` remainder as the rational reference. Factorials, coefficients and
remainder bounds are themselves enclosed. Chain rules propagate the first three
derivatives; arguments outside ±8 are unsupported.

The Python interface encloses rational inputs before conversion, checks shapes,
uses contiguous owned buffers and rejects unsupported operation codes. It
records hashes of both C++ sources, compiler flags/version and the compiled
binary. Tests compare against exact rational derivative enclosures and check
square-root endpoints by independent exact squaring at extreme scales.

These bounds concern ideal mathematical operations under supplied input
intervals. They do not bound the execution error of the separate native flight
integrator or qualify a full flight, clock partition or receiver/IMU error law.
