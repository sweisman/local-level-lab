# Bind accelerometer packets to the same GPS windows

Use the two prepared aircraft recordings and the previously saved 30-second
GPS windows. Keep windows wholly on one side of the training cut. Preserve
crossing and unsupported windows in the table and leave their force fields
empty. The longer window is used because the three GPS solutions disagreed
less on its required force than on shorter windows.

Keep only whole accelerometer packets guaranteed inside the first and last
GPS fixes of each window under both the nominal 200 Hz clock and elapsed
header intervals, for every common offset from −0.15 to +0.15 seconds. Use
the same packet identities under both clocks. Use the sealed physical scale
and a declared half-count error on each accelerometer axis. Report
duration-weighted bounds on the magnitude of the integrated packets under
each clock. Do not use gyro or fused navigation observations, assumed
orientation rates, or an averaging reduction of the count-error bound.

Describe count-bound widths and clock changes alongside the size of the
GPS-only shape contrasts. These quantities give a scale comparison. A
packet average and the GPS force at the center of a window are different
quantities, and they must not be subtracted here. This audit supplies common
time support for a later matched comparison. It does not calibrate error,
impose an upper bound on continuous force, or decide Earth shape.

Freeze the source and input hashes, one numerical thread, 1,112 GPS window
rows, 225,000 source packets and up to 6,200 whole packets per window per
clock. Read only the saved inputs. Run no navigation solves or fits.

[GPS support split](SUPPORT_POLICY.md#keeping-training-and-later-force-windows-separate) ·
[Packet magnitude bounds](QUANTIZATION.md).
