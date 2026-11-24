# Check what GPS geometry survives an antenna-plane screen

Reuse ESA 187's saved two-minute carrier score, receiver path, satellite
products and gyro motion bounds. First reproduce the original carrier
geometry and score weights. Preserve the original score, exact anchor
locations and measurement times in every replay.

Apply three fixed screens using the previous 0°, 5° and 10° starting tilt
allowances. For each half-second satellite pair, require elevation at
both endpoints to exceed the corresponding possible tilt by at least
1°. The extra degree is a fixed screen margin. The screen uses positions,
satellite directions and the declared tilt bounds.

After screening, subtract each interval's mean again to remove the
common receiver clock. If fewer than two satellites remain, the interval
contributes zero range rows, leaving its time on the motion grid. Report
the satellite counts, the number of intervals with at least four usable
satellites and the new score sensitivity to range and motion errors.
Compare the conditional range error allowances at the earlier
illustrative acceleration under exact anchors. This is a geometry
check. An installed-antenna phase calibration and an independent
aircraft error law are separate requirements.

Use one task with one numerical thread, 245 charged calculations and at
most 90 seconds. Use saved sources from development flight 187, zero
new fits, zero original data reads and zero reserved-flight reads.
