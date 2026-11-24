# Balance range and motion error in the saved ESA comparison

Keep the four satellite sets from the [antenna-plane screen](ESA_CARRIER_ELEVATION_SCREEN_RESULT.md),
the same position score, the same six exact position anchors and the same
illustrative acceleration allowance. Any weights on the linear ranges
leave a remainder on the position score. Bound the range term by the
weight norm and bound the remainder using the continuous position-error
response to acceleration between each pair of anchors.

The response is piecewise linear as a function of acceleration time.
Use two-point Gauss quadrature between every range, score and anchor
time to integrate its squared norm. Add contributions from the range
and score weights before taking that norm. Allow velocity jumps at the
exact anchors in this bound. The resulting allowance covers the larger
class, which includes smooth paths with continuous velocity.

For each satellite set, independently evaluate the old weights, then
solve a fixed family of damped least-squares problems. Use damping
ratios of 0.00001, 0.00003, 0.0001, 0.0003, 0.001, 0.003, 0.01,
0.03, 0.1, 0.3 and 1 relative to the largest singular value of the
acceleration-response matrix. Choose the weights with the largest
verified range error allowance. Recompute each bound directly from
its weights, including the original score query times. The best
tested allowance need not be the global optimum.

Run one task with one numerical thread, 293 charged calculations
and a 120-second wall cap. Use the already sealed ESA 187 inputs,
zero new physical-model fits, zero original sensor reads and zero
reserved-flight reads. This comparison still assumes exact anchors
and linear range geometry. Actual antenna and aircraft error limits
require independent evidence.
