# Same-window force comparison across GPS processing methods

Use the sealed positions from the same two flights and 1,112 time tags
already fixed for the GPS reconstruction. At each target, use the same
original epochs and equal-weight quadratic for onboard GPS, L1 code
and dual-frequency code. Keep the fixed 10-, 20- and 30-second window
widths. Require all three position streams, at least five epochs, both
window edges supported within 1.5 seconds and no gap above 1.5 seconds.
Reject incomplete windows and retain their dispositions.

Compute the required force vector for all four geometry and field
combinations using the fixed gravity and disc radius from the shared
height-error diagnostic. Compare force magnitude and the signed
globe-minus-disc magnitude under the same field. For each separately
processed GPS solution, also exchange only its height into the onboard
trajectory. This checks how much of the processing sensitivity goes
through height. Use exactly the same polynomial for these height-only
controls.

The finite limit is 3,336 windows and 66,720 analytic force predictions.
Use one numerical thread and no position solves, new GPS data, inertial
observations or Earth-model fits. Compare force ordering and disagreement
within each recording and window width. Publish every disposition. The
two GPS reconstructions share measurements and satellite corrections.
Their spread is a sensitivity result under the tested coordinate
construction rather than a calibrated bound on the true trajectory.
