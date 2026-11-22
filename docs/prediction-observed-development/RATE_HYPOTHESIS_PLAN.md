# Saved-rate sampling check on ESA development recording 187

**Question:** How much do the constructed angular and velocity increments
change if the logged iMAR rates represent the preceding interval, the next
interval, or point samples joined linearly?

Read only the sealed 20-minute development interval already saved for the
ESA continuation. Verify its manifest and input hashes, original sample
count, timestamp order and saved linear-point increments. Independently
recalculate left hold, right hold and linear-point increments from the
preserved original rate values and actual elapsed times. Compare signed
cumulative differences at the frozen training cutoff and full-interval end,
as well as absolute differences that cannot cancel. Do not alter the original
arrays or choose a method by its Earth-model fit.

This is a **component-integral diagnostic**, with zero new fits, native
propagations, original-file reads or protected-group reads. A small net
increment difference does not bound the resulting aircraft-position error:
rotation composition, force direction and coning/sculling can matter. A
separate fixed-parameter native propagation would be required to test
position sensitivity, followed by reoptimized matched fits before choosing
a sampling interpretation for scientific work. No Earth-model decision or
instrument sampling phase is established here.
