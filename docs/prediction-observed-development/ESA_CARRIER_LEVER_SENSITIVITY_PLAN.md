# How antenna placement affects the two-minute ESA score

Use the fixed receiver score and earlier position anchor from the
[carrier sensitivity check](ESA_CARRIER_SCORE_BOUND_RESULT.md). Use the
sealed iMAR angle increments from ESA development recording 187. A constant
error in the assumed distance and direction from the IMU to the GPS antenna
causes a varying position error when the aircraft turns.

1. Compose the logged increments from the exact anchor to each of the 120
   saved score times. Within a packet assume a constant angular rate.
2. Express the saved score weights in Earth-fixed Cartesian coordinates
   using the local coordinate derivative along the saved receiver path.
   Remove the position error at the starting anchor.
3. Bound the linearized score change per metre of fixed offset error for
   any starting orientation and offset direction. Also report how much the
   bound grows under a separate angular uncertainty that increases at one
   nominal background-field rate from the anchor.

Use one local task with one numerical thread, at most 37,000 packets and
two charged calculations. The worker has 60 seconds. Read only saved data
from the open development flight, with zero new fits and zero reserved
flight reads. Verify timestamp alignment, rotation order, the coordinate
derivative and the sign-independent bound in deterministic tests.

The bound is a sensitivity to the measured change in orientation, the
first-order position mapping and the declared angular uncertainty. The
campaign's published separation of about 2.12 m is context for the size
of the installation. The actual offset error, flexibility of the mount,
receiver tracking errors and absolute anchor accuracy require separate
evidence.
