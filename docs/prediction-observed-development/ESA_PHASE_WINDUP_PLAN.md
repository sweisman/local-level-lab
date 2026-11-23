# Can aircraft antenna rotation change the saved range score?

GPS phase changes when an antenna rotates. Some of that change is common
to all satellites at a given instant. The saved score removes such terms.
This check measures how much tilt remains possible within the score budget
under the ideal crossed-dipole model. [Original phase model](https://ntrs.nasa.gov/citations/19920060722)

Use the saved 240 half-second satellite lists, their 2,496 signed weights,
and the corresponding Nuuk Museum projection. All three inputs have fixed
hashes in the published error budget. Calculate the same bound separately
for the full score and its parts covered and missed by the ground
comparison. Transform weights from intervals to endpoints before taking
absolute values, so shared intermediate epochs cancel where the weights
permit. Compare each bound per degree of maximum tilt to the original
score gap. Use the separately hashed published error budget to calculate
how much tilt would consume its example allowance in the covered part.
That calculation keeps the other example caps in place.

Under the ideal model, a rotation about the antenna normal changes every
satellite's phase by the same number of cycles and cancels in the score.
For a tilt from an upright reference, use the upper bound of one radian
of phase change per radian of tilt when every direction remains in the
upper antenna hemisphere throughout the change. Use the combined
GPS L1/L2 coefficient for the same phase addition in cycles to both
bands. The bound applies to the receiver attitude contribution
relative to the upright reference at each endpoint. It does not include
transmitter wind-up or the changing phase of the upright reference.
[ESA measurement equations](https://gssc.esa.int/navipedia/index.php/Carrier_Phase_Wind-up_Effect)

Validate the derivative against independent finite rotations and verify
that interval and endpoint sums agree. The replay has three calculations
on the same 240 blocks, at most 2,496 values each. It uses one numerical
thread and saves input, source and environment identifiers. There are
zero new fits, selections or reads of reserved data. Actual in-flight
tilt, orientation-dependent antenna calibration and reflection errors
remain separate evidence requirements.
