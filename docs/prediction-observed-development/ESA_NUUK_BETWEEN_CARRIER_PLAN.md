# Check the between-sample displacement against aircraft carrier phase

Use the [zero-at-Nuuk-times displacement](ESA_NUUK_BETWEEN_SAMPLES_RESULT.md)
and the same 240 half-second AIR1 pairs, recorded signal masks, satellite
navigation and final clock products as the [previous aircraft replay](ESA_SHARED_MOTION_CARRIER_RESULT.md).
The saved path and the alternative have identical position at the four
ground checks. This replay uses the intervening aircraft observations.

At the original and displaced aircraft positions, calculate the signed
range correction needed to keep each received phase difference unchanged.
Allow one common clock change per pair. Keep the original transmit times,
navigation and neutral-atmosphere correction fixed in this geometric
shift. Also calculate the measured ionosphere-free phase residual on the
original fixed path using broadcast clocks and the atmospheric model at
the actual saved positions. Add the signed geometric correction to obtain
the residual on the displaced path. Report residual RMS for both paths,
the number of pairs with larger residual RMS and how much of the required
pattern the archived clock update supplies where available.

Charge one bounded setup and 240 pair operations with at most 66 work
steps per pair. Use a single worker and thread and a 180-second cooperative
cap with the existing qualified finite technical recovery. Use no new
receiver or inertial fit and no reserved recording. Only the constructed
motion is interpolated. The carrier data were used to estimate the saved
aircraft path. Agreement there does not supply independent error coverage.
