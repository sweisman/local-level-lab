# Check the effect of the GPS antenna offset on force directions

The matched direction-change test uses acceleration measured at the
iMAR and predicted from the GPS antenna trajectory. When the aircraft
turns, the two locations accelerate differently. Test that effect on
the same eight sealed windows, two widths and three matched field
assumptions as the previous direction comparison.

Use the published iMAR-to-antenna vector in aircraft axes
\((-1.24,-0.64,-1.60)\) metres. The campaign estimates this vector from
integrated inertial and GPS observations. Treat it as one fixed working
value, without fitting it or transferring any estimated precision.
The campaign's published roll and pitch come from the same iMAR.
The GIRAFE instrument supplies a separate vertical force measurement.
Neither product supplies a verified independent three-axis attitude
reference. [Campaign methods and Table 1](https://essd.copernicus.org/articles/17/1667/2025/#section2)

In the common starting frame, antenna velocity relative to the iMAR is
the rotated cross product of the body angular rate and the lever arm.
Estimate the angular rate at packet edges from the adjacent midpoint
rates on the recorded clock. Difference the relative velocities across
each packet and divide by its actual duration. Add that average
acceleration to the iMAR force mapped into the same frame. Neglect the
gravity difference across the two-metre offset in this sensitivity check.
Use the same gyro data for both shapes and compare the same predicted
angles with unadjusted and corrected force. Reproduce the saved
unadjusted angles before releasing the scores.

First verify the correction with known constant and varying rotations
on uneven packet intervals. Use a shared lever-arm helper and the
existing direction-window reader. Freeze one packet pass per window,
at most 121,000 packets each, one numerical thread and a 120-second
limit. Use closed development inputs and the previously calculated
angles. Preserve all results. No reserved flight, new fit, absolute
error calibration or independent confirmation.
