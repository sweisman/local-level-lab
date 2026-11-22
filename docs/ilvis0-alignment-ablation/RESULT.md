# Alignment-status screening ablation

The fixed ablation scanned 29 sources previously selected by receiver/raw support. 29 passed strict parsing and 0 were retained as invalid or unsupported.

With the fused alignment-status veto removed, but the original speed, climb, roll, course-rate, gap and raw-completeness checks retained, it found **5 candidate stretches** totaling **55.0 minutes** on **4 recorded-date groups**.

The [candidate table](candidates.csv) lists every recovered interval. The [file ledger](files.csv) also records sources with no candidate. No gyro model residual was inspected and no Earth-model fit was run.

**These are not newly eligible scientific flights.** Group 1 motion comes from a fused navigation solution; its roll, climb and course values may be less dependable when its own alignment flag is false. A separate receiver-motion check and full nuisance-information gate are required before fitting. The original 53-stretch study remains unchanged.

