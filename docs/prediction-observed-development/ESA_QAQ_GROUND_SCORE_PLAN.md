# Compare the Qaqortoq one-second ranges with the aircraft score

Use the frozen two-minute development interval of ESA flight 187 and the
public Qaqortoq observation excerpt already verified for exact overlap. The
ground station is 456–458 km from the aircraft. The aim is to measure their
common satellite-range behavior. Local atmospheric and antenna errors could
differ substantially at that distance.

Use common GPS `L1C` and `L2W` on exact successive whole seconds and keep only
arcs with both intervening aircraft half-second pairs. Apply the same numerical
limits as the existing aircraft continuity checks to the ground Doppler and
dual-phase differences, using the ground's actual one-second interval. Use the
final orbit and clock products, independent ground position from the receiver
header, and the common neutral-atmosphere model. Require at least five usable
satellites in each admitted interval. The aircraft path and score weights stay
fixed.

Report the fraction of score weights supported by the measured intervals and
the signed score equivalents of the aircraft, ground and aircraft-minus-ground
range residuals. Report unsupported intervals as missing. The comparison gives
no absolute aircraft position or error calibration.

One task, one thread and a 180-second cooperative cap. Charge one setup and
120 one-second checks. No models are refitted and reserved flights remain
sealed. The earlier checked task recovery handles technical interruptions.
