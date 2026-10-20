# The common acceleration polynomial passes its component checks

All **18 generated identities pass**, covering three reference-force samples,
three calibration centers and two orientation domains. The independent
Rodrigues/engineering-unit formula agrees at all 1,152 parameter points. All
972 derivative evaluations and 4,608 polynomial checks pass. The complete
27 physical plus 15 auxiliary columns remain.

This validates the component identity and its conservative common-error radii.
It does **not** yet propagate a trajectory with those terms separated. A native
candidate must preserve the actual midpoint dynamics, changing attitude and
coordinate metrics, field/transport contributions and complete packet clock.
Its factored remainder and expanded joint interface need their own qualification
before another usefulness comparison.

No native evaluations, observed fits, original recordings or protected ESA
outcomes were used. Existing numerical model preferences are unchanged; no
observational uncertainty or detection claim follows from these controls.

[Sealed results](README.md) · [Frozen scope](PLAN.md) ·
[Component derivation](../ilvis0-reference-acceleration/PLAN.md) ·
[Native construction requirements](../ilvis0-reference-acceleration/NATIVE_PLAN.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
