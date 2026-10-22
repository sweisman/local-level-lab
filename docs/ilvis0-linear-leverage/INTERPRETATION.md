# Five training epochs leave substantial freedom

The two completed long-record cases have two separate limitations:

- Their approximation bounds grow too wide during integration.
- Five training epochs leave considerable calibration freedom in a simplified
  linear calculation, even before those approximation errors are included.

The saved linear check finds feasible horizontal spreads of **420–1,068 m**.
The long-record test's fixed horizontal width target is **20 m**. Each saved
point satisfies the linear training constraints exactly, within the original
physical parameter box.

These are generated-data diagnostics, not aircraft errors. The linear points
have not been checked in the nonlinear model. They do not prove the physical
target impossible, but they show why improving one remainder is not enough
evidence to promise useful prediction ranges.

The next design should compare training coverage using the intended earlier
record, rather than rely on five sparse epochs. The earlier prediction plan
used 292 training epochs. Any new calculation needs its own finite freeze;
the running study keeps its original five epochs and targets.

[Verified calculation](README.md) · [Next diagnostic](NEXT_PLAN.md) · [Current work](../NEXT_STEPS.md)
