# Matched geometry check for the candidate stopping rule

Question: Does the research-only one-sided numerical rule behave consistently
across all three physical candidates when the same generated measurements are
fitted on a straight route and a turning route?

Freeze two 120-second generated recordings at 55° north, one straight and one
turning, both level. Use the same increment-noise law, seed, calibration bounds,
clock, receiver error model, training split and start in both. Each recording
gets three fits against exactly the same IMU increments and earlier receiver
positions. Save every fit, including failures, before opening later receiver
positions. Apply the identical one-sided rule to each candidate. Keep its
original full-correction verdict alongside the new verdict.

This is a six-fit generated development control. Limit each candidate to one
start and 200 native fit evaluations, including nine reserved for final
verification. Use two one-thread workers and a finite cooperative wall limit.
Qualify source tests and task-level interruption recovery before launch. Never
read observed or reserved ESA groups. A failed preflight remains a failure.

Report convergence separately from physical path adequacy and withheld
receiver prediction. The candidate rule qualifies for further aircraft error
law work only if it preserves known controls, applies equally across models,
and avoids accepting physically inadequate forecasts. This control does not
calibrate model significance or authorize observed-aircraft fits.
