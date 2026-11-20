# Compare inertial forecasts with GPS-only extrapolation at four cuts

Use the four training cuts of the [height-error check](ESA_HEIGHT_ERROR_TRANSFER_RESULT.md)
on ESA development recording 187. Score the first 120 receiver reports
after each cut. Use both inertial error laws and report the original raw
horizontal and height RMS. Use both GPS-only controls already defined for
the 400-report cut. One holds the last receiver velocity constant. The
other estimates course change from exactly 60 earlier velocity reports
and holds the turn rate, speed and vertical velocity constant.

Reuse the sealed 400-report [control result](ROLLING_ORIGIN_400_TURN_CONTROL.md).
For the other three cuts, store the two GPS forecasts before opening their
later receiver positions. Retain every cut and both GPS rules. Compare
errors by axis without selecting a preferred rule or changing the original
accuracy outcomes. Check that the source clocks and receiver sequences
match the original forecast inputs.

Use three task identities, two charged extrapolations each, one numerical
thread and a 90-second cooperative limit. Use zero new navigation fits,
native integrations, original-file reads or reserved-flight reads. This
development comparison measures improvement over two specified baselines
on one flight. It leaves absolute adequacy, gyro-only attribution and
independent-flight prediction coverage open.
