# Check whether the ground stops can exclude the X-axis bias

Reuse all 45 and 30 sealed minute-mean accelerometer vectors from the
two receiver-selected ground stops on recording 187. Give each stop
its own unknown constant force magnitude. This avoids supplying a
gravity prediction or borrowing a calibration from an Earth-model fit.

Compare nominal calibration and the +0.10 m/s² X endpoint with the
other terms fixed. Then minimize the maximum within-stop squared
force spread over the six original accelerometer bias and gain terms.
Do this for each stop alone and for both with one shared calibration.
Repeat with X bias fixed to the endpoint. Use the variables
(s_i=(1+g_i)^{-2}) and (p_i=s_i b_i). After subtracting the common
terms, squared force at each minute is linear in (s_i,p_i), and
the physical box gives linear constraints on those variables.
Recompute each candidate's corrected force from its bias and gain
values and verify the working limits.

Check the calculation on constructed varied orientations with a
known offset. Freeze one thread, all 75 existing vectors and at most
six linear programs with 2,000 iterations each. Read no original
files, use no model fits and keep all reserved recordings closed.
Within-stop scatter tests whether these observations offer leverage.
It cannot set an absolute bias bound without independent limits on
ground motion, temperature changes and force-measurement error.

[Earlier ground stop result](ESA_GROUND_FORCE_SUPPORT_RESULT.md) ·
[Reversing calibration endpoint](ESA_GYRO_DIRECTION_CALIBRATION_RESULT.md)
