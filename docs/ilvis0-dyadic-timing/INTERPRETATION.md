# A modest speed improvement on matched short inputs

All four calculations completed, and both implementation pairs produced
identical results. The integer version took 3.92 rather than 4.40 seconds
under fixed-zero removal, and 2.88 rather than 3.17 seconds under profiled
removal: about **9–11% faster** in these short cases.

The preregistered engineering screen passes. Each case ran once, so this
does not establish a general performance guarantee. The separately frozen
six-source full-history screen now tests the original 120-second bound limit
on the actual training-restricted domains. It cannot replace missing regions
in the completed prediction comparison or qualify its width target.

[Verified timings](README.md) ·
[Full-history scope](../ilvis0-dyadic-range-preflight/PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
