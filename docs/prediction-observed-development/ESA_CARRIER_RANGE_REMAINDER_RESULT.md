# How much does linearizing the carrier geometry change the score?

For the two-minute ESA development window, we can now calculate an upper
bound on this approximation error once the position and motion error limits
are known. With **1 m of position error per coordinate** at the six reference
times and **0.002 m/s² RMS** acceleration of that error, the geometric
linearization contributes at most **0.27% of the saved score gap**. Those limits
are illustrative and remain unmeasured for the aircraft.

Let \(E\) be the anchor error limit in metres per coordinate and \(A\) the
RMS acceleration limit in \(\mathrm{m/s^2}\). At the recorded times the
coordinate error is bounded by \(E + 260 A\) metres. The coefficient 260
comes from the 120-second window and its largest 30-second interval between
anchors. The resulting geometric error in score units is at most

\[
5.153\times10^{-5}(E+260A)^2.
\]

The calculation checked all **4,992 satellite positions** at the original
pair endpoints. Their distances from Earth's centre ranged from 26,221 to
27,028 km. The bound uses wider domain limits and holds while the displaced
height stays within 100 km of the reference ellipsoid. The second derivative
bound includes the geometric range and Sagnac correction. Satellite transmit
times, clock terms and modeled atmospheric delays stay fixed. Errors in those
quantities still require support in the carrier error budget.
[Combined reference error budget](ESA_REFERENCE_ERROR_BUDGET.md)

Seven software tests passed. The [frozen plan](ESA_CARRIER_RANGE_REMAINDER_PLAN.md)
closed with 242 of 242 checks, zero fits and zero reads of reserved flights.
The exact rational coefficient was reproduced from the saved signed weights.
The [result](esa-carrier-range-remainder-result.json) has SHA-256
`8db0d4ae89708015fa6b8026aac2da522fbbb4aabd64f0f9501ad722abc67844`.
