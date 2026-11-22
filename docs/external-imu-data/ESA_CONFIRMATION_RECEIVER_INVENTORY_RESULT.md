# Receiver coverage for the reserved ESA flights

**All seven reserved flight groups have at least one provisional window.**
The receiver screen identified ten continuous windows from eight GPS exports.
They run from 22.5 to 346.7 minutes each and total 34.7 hours. Every window
passes the existing receiver-quality, speed, duration and distance screens.
IMU timing and completeness still need to be verified for each window before
it can be selected for confirmation. [Selection rules](ESA_SELECTION_V2.md)

The later [timestamp audit](ESA_CONFIRMATION_TIMING_RESULT.md) verifies a
20-minute slice in each group. It leaves the rest of the provisional coverage
and aircraft prediction uncertainty open.

| Archive recording | Receiver epochs checked | Provisional windows | Total minutes |
| --- | ---: | ---: | ---: |
| 178a | 26,589 | 1 | 90.5 |
| 178b | 16,954 | 1 | 22.5 |
| 179 | 54,969 | 1 | 346.7 |
| 180 | 46,630 | 1 | 310.8 |
| 182 | 85,156 | 3 | 497.2 |
| 183 | 44,624 | 1 | 288.0 |
| 184 | 41,669 | 1 | 273.4 |
| 186 | 43,298 | 1 | 253.2 |

Recordings 178a and 178b belong to the same flight group. The three windows
from recording 182 also count as one group. The screen used 359,889 receiver
epochs. It used no reserved inertial data or Earth-model outcomes. The
aircraft error model and prospective confirmation protocol still need
qualification before any model fitting. [Confirmation grouping](../PROVENANCE_VERIFICATION.md)

The first run stopped at work accounting. The second screened five exports
and preserved three UTC-format failures. The third processed only those
three files after adding support for single-digit UTC hours. All 63 focused
tests passed. The stages retain their original charges and results.
[Accounting correction](ESA_CONFIRMATION_RECEIVER_INVENTORY_ACCOUNTING.md) ·
[UTC-format correction](ESA_CONFIRMATION_RECEIVER_INVENTORY_TIME_FORMAT.md)

The [combined result and exact intervals](esa-confirmation-receiver-inventory-v3-result.json)
have SHA-256 `5055f518e0bce4b7121f0ca591f0694ec605ac81dc123a49d14923b51f46963b`.
The frozen acquisition receipt records the archive location, byte count and
SHA-256 for each original receiver export. Reproduce the report from the
closed studies without rereading the original receiver or inertial streams.
[First evidence package](esa-confirmation-receiver-inventory-v1-evidence/README.md) ·
[Second evidence package](esa-confirmation-receiver-inventory-v2-evidence/README.md) ·
[Third evidence package](esa-confirmation-receiver-inventory-v3-evidence/README.md)

```sh
env PYTHONPATH=analysis ~/venv/bin/python -m lll.esa_confirmation_receiver_inventory report
```
