# Bound the geometric approximation in the ESA carrier score

Use the existing two-minute score, its position chart, the six reference times
and the original signed carrier weights. Recheck the final orbit locations for
all accepted transmit times. Use a derivative envelope for the exact WGS84
coordinate-to-range calculation, including the fixed-position Sagnac term.
Hold transmit times, satellite clocks and the modeled atmosphere fixed,
as in the carrier comparison. Treat changes in those terms separately.

For either endpoint of a carrier pair, integrate a bound on the second
derivative along its position perturbation. Sum the endpoint bounds with
the absolute receiver-clock-centered carrier weights. Use rational arithmetic
for this step. The rational bound is conditional on anchor position error and
RMS acceleration of the displacement. Report the quadratic coefficient and
an illustration with 1 m anchor error per coordinate and 0.002 m/s² RMS
acceleration. These numbers illustrate the geometry and do not set actual
instrument error limits.

One task checks 240 pairs with one numerical thread and a 180-second
cooperative cap. Charge one setup, 240 geometry checks and one bound
calculation. Run no fit and use no protected flight. Technical recovery
uses the verified finite procedure.
