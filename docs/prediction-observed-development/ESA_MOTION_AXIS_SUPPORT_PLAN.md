# Which motion measurements can constrain the saved ESA score?

Use the original two-minute score and its closed displacement with the
four Nuuk position anchors. Split the exact position score and RMS
acceleration energy into north, east and up in the saved local metric.
Replay the original case, then constrain the displacement to each axis
and to the horizontal plane. Scale only the original allowed components
to span the same score gap. Reintegrate them and confirm the unchanged
zero anchors, endpoint velocity and exact score shift. Report the required
RMS acceleration and peak position for each case. A zero allowed score
component means that case cannot span the saved gap.

Separately check the clock and atom interrogation metadata from the
already-opened GIRAFE file on the nominal carrier interval, GPS week 2269
seconds 388614–388734. Summarize coverage before evaluating force. The
acceleration channels are never scored in this study. The atom channel
measures near-vertical specific force. The idealized up-only kinematic
constraint is a separate diagnostic and neither verifies its accuracy nor
assumes they are interchangeable.

Use one task and one numerical thread. Allow the original integration and
five case replays of 125 acceleration knots, plus one GIRAFE scan of at
most 50,000 rows. Bind
the sealed parent, exact dataset hash, tests and technical recovery before
launch. Preserve the original fits and witness. Use no new fits or reserved
flight data. This establishes the scope of the motion check and does not
calibrate any of the aircraft error caps.
