# What slows down the ESA packet bounds

Both 470-packet profiles reproduced the two original bound reports byte for
byte, with identical packet-work counts. Nearly all the time was spent
advancing the packet state. No single calculation dominated the run.

| Measurement | Zero-field globe | Zero-field disc |
| --- | ---: | ---: |
| Process CPU with profiler | 63.24 s | 61.49 s |
| Elapsed time with profiler | 64.08 s | 62.80 s |
| Packet advance, including its calls | 62.05 s | 61.19 s |
| Transport increments, including their calls | 18.04 s | 18.17 s |
| Buffer-address conversion, including its calls | 4.73 s | 4.80 s |
| Exact affine radius, including its calls | 3.46 s | 3.49 s |

The times include profiling overhead. Nested function times overlap. Buffer
addresses were converted 765,346 times per candidate. The exact affine
radius was evaluated 2,826 times, repeatedly converting the same calibration
box widths. Reuse those exact widths first and compare complete CPU time and
bound bytes. The array interface and transport operations remain separate
opportunities. These measurements do not establish full-history runtime.

The two tasks ran serially in 139.5 seconds, restoring the complete archived
source package for each calculation. They used two bound charges and no
model fits, new receiver data, or reserved flights.

- [Frozen plan](ESA_PACKET_BOUND_PROFILE_PLAN.md)
- [Profile tables and bound hashes](esa-packet-bound-profile-result.json)
- [Verified evidence](esa-packet-bound-profile-evidence/README.md)
