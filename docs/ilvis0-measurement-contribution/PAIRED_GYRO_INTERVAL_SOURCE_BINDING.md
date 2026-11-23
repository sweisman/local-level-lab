# Bind the rotation comparison to the 24 October recorder pair

The first [interval study](PAIRED_GYRO_INTERVAL_PLAN.md) stopped before
the interval comparisons. The 2009 mixed pair inherited from the gyro
clock study came from 20 October, while the force-direction calculation
used 24 October. The failed study and its charged work remain sealed.

Use shared leg `leg-590ee7971efb` in the original overlap table. Require
IMU8 `3df34ea39a6cbdbe15bb0f36` and IMU21 `233183f67270980491416678`
from the 24 October flight. Bind both uncompressed source hashes and
the exact overlap from 13:25:59.003645 to 13:36:59.693758 UTC before
decoding. Confirm the IMU8 provenance against the force study before
replaying the original packet selection. Match the intervals and apply
the same allowances, 32 cases and 90-second limit from the first plan.
Zero interval comparisons or model fits were obtained in the first run.
