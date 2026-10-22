# Geographic and midpoint derivative propagation

`analysis/lll/ilvis0_path_geometry.py` carries actual derivatives of orders
0–3 through the globe/disc coordinate metrics and transport equations.
Sine and cosine values use degree-40 scalar Taylor polynomials with remainder
at most `|x|^41/41!`, for `|x| <= 8`. Their derivatives use the chain rule.
Positive square roots use exact integer square-root tests on a 128-bit dyadic
grid; higher derivatives follow by differentiating `y²=x`.

Geographic coordinates require latitude within ±1.57 radians and positive
north/east metric factors. Unsupported domains fail. Constants match the native
binary64 inputs; this does not prove the accuracy of native arithmetic.

`analysis/lll/ilvis0_path_motion.py` applies the original midpoint equations:

1. Compute initial coordinate rates and midpoint coordinates.
2. Compute background/transport terms and a trial velocity.
3. Recompute rates using midpoint coordinates and mean trial velocity.
4. Repeat the local rotation/velocity solve, then update coordinates with the
   revised rates.

Each local solve uses left navigation-frame and right sensor-frame rotation
increments. The force uses the midpoint attitude. The velocity solve retains
the native cross-product inverse, including its sign and denominator. Upstream
removal uses the same conventional vector for every physical candidate.

Native Rodrigues rotation uses a polynomial when squared argument norm is
below the native binary64 `1e-4` threshold; otherwise it uses sine and cosine.
The interval implementation retains both formulas and rejects a domain
straddling the switch. It does not replace the polynomial by an exactly
orthogonal rotation. Switch completeness and one-sided changes still need
qualification before a whole-history claim.

Intermediate results are rounded outward to a 96-bit dyadic grid. Integer
floor/ceiling operations prove containment for each rounding; accumulated
enclosure width remains visible. This bounds the ideal real-arithmetic
expressions under supplied input derivative bounds. It is not a bound on the
difference between those expressions and native floating-point execution.

Independent controls include metric series at the equator, exact noncommuting
rotation derivatives, scalar trigonometric series, known acceleration/gain
responses and stationary controls for all candidate/processing combinations.
They do not establish useful uncertainty over an eight-minute history.

`analysis/lll/ilvis0_path_packets.py` connects normalized parameter paths to
the initial state, every preceding full packet, the declared partial packet
and the receiver lever arm. It checks all 27 columns and rejects a query range
leaving the declared branch. Cumulative packet starts follow the native
binary64 convention; integration periods retain the supplied values. This
distinction is explicit and does not bound native numerical execution error.
Separate finite packet/time limits prevent an accidental full-history run.
