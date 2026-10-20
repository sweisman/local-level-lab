# Separate coordinate bounds now survive the native controls

All 24 generated native controls pass: six derivative, six packet-boundary,
six broad-domain and six stationary-motion cases. The study used its 78 native
evaluations and 348 propagation bounds, completing in 348.86 seconds. All
physical and shared-error columns remain present.

The candidate keeps both separate coordinate bounds and useful global norm
bounds through force, velocity and position calculations. It reuses immutable
validated views and caches repeated exact norms. Local tests compare every
returned bound bit for bit with the earlier rational implementation and check
the training-conditioning path independently.

The earlier implementation passed 20/24 controls and missed four per-bound
time limits. Its failures remain preserved. The new freeze uses two workers
with two numerical threads each, reducing competition within each bound's
unchanged 60-second limit. Its numerical limits and total four-thread ceiling
are unchanged. The completed studies are not a controlled wall-time benchmark
of caching alone.

This qualifies transport of coordinate bounds. The tighter norm-constrained
body-source interval has not yet been installed. Connecting it at the correct
packet midpoints and endpoints is next; complete prediction-width testing and
aircraft validation remain downstream. No aircraft fit or protected ESA data
was used, and the existing aircraft findings are unchanged.

[Results and evidence](README.md) · [Next integration task](NEXT_PLAN.md) ·
[Earlier failed implementation](../ilvis0-component-transport-controls/README.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
