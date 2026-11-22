# Search for a second ground interval in the opened ESA recording

The first speed-selected interval occupies receiver indices 0–7814 in the
verified [ground control](GROUND_RECEIVER_CONTROL_RESULT.md). Read the same
hash-verified GNSS-only PPP export and consider every report from index 7815
to its end. Apply the **identical** horizontal speed ≤0.5 m/s, absolute
vertical speed ≤0.2 m/s, adjacent gap ≤1 second, and minimum 600-report rule.
Choose the longest qualifying later run, breaking a length tie by earliest
start. Do not inspect later IMU values, model results or position scatter
before selection. If none qualifies, record that outcome; do not relax the
rule. Use the existing relative-position summary only after selection.

Save original source and prior-selection hashes, selected indices/times,
speed and relative-position summaries, or the explicit no-run result. This
receiver-only development check has zero fits and no protected-group reads.
Any later IMU comparison must use only the timestamp overlap and must not
assume the same aircraft orientation, physical location or sensor bias.
