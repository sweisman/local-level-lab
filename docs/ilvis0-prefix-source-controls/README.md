# Reusing a verified source prefix

The reference, interval-derivative and point-derivative source streams can now copy a complete prefix and finish a different query without repeating its earlier packets. The comparison uses generated sources and independent original cold kernels.

| Source stream | Cases passed | Tail frames checked | Exact array comparisons |
|---|---:|---:|---:|
| reference | 6/6 | 396 | 792 |
| interval | 6/6 | 396 | 1188 |
| point | 6/6 | 396 | 792 |

The planned checks cover nonuniform packet periods, nonzero/asymmetric clock support, query knots and adjacent values, every parameter column and both midpoint/end phases. Copying must leave the parent unchanged. Clipped histories, a query reaching back into its prefix and changed reference bindings must be rejected. Packet allowances are preserved.

**Scope: source copying only; complete native reuse remains unqualified.** The source calculations are shared by the Earth candidates; this is not a model-comparison result. The complete geographic, velocity, force-integral, common-clock and conditioning states still need equivalent treatment. No aircraft integration or fit was performed. V01 remains unqualified.

[Fixed scope](PLAN.md) · [Design](../ilvis0-prefix-reuse/DESIGN.md) · [Remaining complete-state work](../ilvis0-long-remainder-feasibility/PREFIX_REUSE_PLAN.md)
