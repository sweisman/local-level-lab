# Check the aircraft GPS ranges while parked in Nuuk

Use the validated 256 KiB prefix of the original AIR1 receiver file
and the saved receiver-selected Nuuk stop. Use complete half-second
records from GPS second 383697.0 through 383715.5. Require a following
epoch marker to check completeness. These records precede the iMAR
coverage of the stop, so the range check assumes the parked position
was fixed over this excerpt.

Reconstruct the approximate antenna position from the earlier apron
reference and the saved receiver offset. Reuse the same broadcast
navigation, final GPS orbits and final satellite clocks as the airborne
range check. Compare consecutive dual-frequency carrier readings with
the predicted ranges at the fixed position. Preserve the original
slip, declared receiver time and satellite screens. Remove common
receiver clock changes. Also combine adjacent half-second residuals
on the same satellites, using integer GPS times, to report the
one-second range RMS.

Repeat the calculation with a fixed five-metre position shift in each
positive and negative local axis. This tests sensitivity to the
assumed parking position. It establishes no position uncertainty limit.
Report the RMS and comparison across shifts for all the retained
observations. Report any absent satellite products or unqualified pairs.

The result describes the installed system on the apron in a short
interval. It includes remaining satellite and propagation errors
and cannot establish the aircraft's range error during turns.
Use one local thread, 260 charged checks and a 60-second wall cap.
Use no new downloads, model fits or reserved aircraft observations.
