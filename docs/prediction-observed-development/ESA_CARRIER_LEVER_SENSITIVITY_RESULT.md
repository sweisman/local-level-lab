# A fixed antenna offset would need at least 40 cm of error to close the score gap

The two-minute comparison on ESA development flight 187 would need a
fixed antenna-to-IMU offset error of **at least 41.9 cm** to close the
saved score gap using the logged angles. The lower limit is **40.5 cm**
after allowing the angular error to grow at one nominal background-field
rate. A hypothetical **10 cm** offset error could account for at most
**25%** of the gap under that allowance.

The calculation used 36,001 saved gyro packets. The largest change in
orientation from the starting anchor was 21.09° at the 120 score times.
The calculation allows any starting orientation and any constant
direction for the offset error. It removes the initial position offset
at the anchor and uses the local derivative of the receiver score along
the saved path. The offset lower limit leaves open whether any particular
offset can close the gap.

The published antenna-to-IMU separation of about 2.12 m gives the scale
of the installation. The campaign estimated it from the same types of
inertial and receiver observations. It provides no independent error
bound. Absolute anchor position, mount movement, antenna tracking
errors and gyro errors outside the tested allowance also remain open.
[Campaign instrumentation and Table 1](https://essd.copernicus.org/articles/17/1667/2025/#section2)

One task passed, with two charged calculations, zero new model fits and
zero reserved-flight reads. Six deterministic tests covered time order,
partial-packet integration, coordinate scaling and the signed score
bound. The saved receipt can be checked with
`env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_carrier_lever_sensitivity report`.

[Frozen plan](ESA_CARRIER_LEVER_SENSITIVITY_PLAN.md) ·
[Full result and input hashes](esa-carrier-lever-sensitivity-result.json)
