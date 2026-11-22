# Three raw GPS receiver streams agree within millimetres on most intervals

The two additional receivers on ESA flight 187 recorded the complete 400/120
development window. Over the later 120 one-second intervals, the Septentrio
and NovAtel differed by **1.77 mm RMS** in measured carrier-range changes.
Each differed from AIR1 by about **5–6 mm RMS** after removing a common
receiver-clock change at each step.

| Receiver pair | Earlier RMS | Later RMS | Later 95th percentile of absolute differences | Largest later difference |
| --- | ---: | ---: | ---: | ---: |
| AIR1 and Septentrio | 5.15 mm | 5.26 mm | 10.76 mm | 41.89 mm |
| AIR1 and NovAtel | 5.51 mm | 5.60 mm | 11.72 mm | 45.58 mm |
| Septentrio and NovAtel | 1.99 mm | 1.77 mm | 3.83 mm | 6.92 mm |

All three pair comparisons used the same satellites and epochs. There were
at least 11 satellites at every retained interval. The calculation used 398
earlier and 120 later intervals. It excluded the one interval crossing the
archived AIR1 clock step. Individual differences are retained, including the
centimetre-scale excursions in the table. The measurements are differences
of the same GPS L1C and L2W carrier phases between successive integer seconds.

These are errors relative to another receiver, on the same aircraft antenna.
The receiver-specific differences can now be applied to the frozen shape score
on a common geometry. Errors shared by all three streams remain unmeasured.
No new position solution, inertial fit or protected flight was used.

The study retained 2,606 original Septentrio epochs and 522 original NovAtel
epochs, with the original headers. Each source range matched an independently
requested overlap byte for byte. All 519 interval checks and nine focused
tests passed. The range receipts give the byte offsets, lengths and hashes
needed to obtain and verify the exact excerpts.

[Frozen plan](ESA_PARALLEL_RAW_RECEIVER_WINDOW_PLAN.md) ·
[Range receipts and numerical results](esa-parallel-raw-receiver-result.json) ·
[Execution receipts](esa-parallel-raw-receiver-evidence/README.md) ·
[Reproduction bundle](esa-parallel-raw-receiver-evidence/bundle.zip)
