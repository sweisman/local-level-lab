# Finish the one remaining force window

The batched run passed three turning windows. The final turning
window, `turn-41116`, stopped at its cooperative time limit after
117 charged force averages. All original scalar and batched results
remain sealed. A timing check on generated inputs found that the
batched arithmetic takes about 0.09 seconds for 128 force averages
when journal writes are excluded.

In v4, count a matched set of eight force averages at one time
support and one receiver as one operation. Charge every quadrature
point in that set before evaluating it. At most 96 matched sets
contain 768 force averages and 52,224 quadrature points. Use one
thread and a 60-second limit. The source input for `turn-41116` is
identical to v3. Include the original passing records for the other
seven windows and preserve both interrupted attempts and their charges.

[Original design](ESA_GIRAFE_FORCE_CONTRAST_PLAN.md) ·
[Batched calculation](ESA_GIRAFE_FORCE_CONTRAST_BATCH.md)
