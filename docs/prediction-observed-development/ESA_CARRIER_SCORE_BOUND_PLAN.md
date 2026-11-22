# How much carrier error could change the score?

The earlier replay tested one constructed displacement. This check uses the
same two-minute comparison on ESA flight 187 to bound score changes from any
smooth displacement in a specified linear range model. Use the 240 matched
half-second carrier pairs and the common satellite set from the final-product
replay. Keep transmit times, final satellite positions, atmospheric terms and
the saved path fixed. Use the exact score times and weights already frozen for
that comparison.

The calculation assumes zero displacement at the four permanent Nuuk ground
times and both endpoints of the carrier record. It leaves the possible RMS
acceleration of the position error as a variable. The earlier displacement's
acceleration is an illustration. The reference station observations have yet
to establish exact aircraft positions or an empirical acceleration limit.

Construct the sparse signed range sensitivity to position at each carrier
epoch. Remove each pair's common receiver clock. Find range weights whose
transpose reproduces the score weights as closely as possible, and bound any
remaining weights using the position interpolation error allowed between
anchors. Separately bound the effect of score times that lie between carrier
samples. Save the range weights and both sensitivities so the conclusion can
be recomputed. This is a first-order geometry calculation. It assumes no
measured upper bound on the tracking error, and makes no decision about shape.

One task, one thread and a 180-second cooperative cap. Charge one setup, 240
pair calculations and one sparse solve capped at 2,868 iterations. No new fits
or reads of reserved flights. The existing qualified recovery uses a separate
finite allowance only for a technical interruption.
