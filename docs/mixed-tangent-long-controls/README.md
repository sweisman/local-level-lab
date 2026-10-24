# Faster arithmetic: long-record result

**All six cases keep positions and residuals exactly, but none passes the derivative test.**

The prototype takes about one fifth of the reference calculation time on these generated twenty-minute records. It remains unqualified: small errors in parameter sensitivities exceed the fixed tolerance on every case. Existing fitting methods and published scientific results are unchanged.

| Generating candidate | Processing case | CPU speed ratio | Derivative entries outside tolerance |
|---|---|---:|---:|
| sphere_rotating | Zero removal | 4.70× | 65 |
| sphere_rotating | Profiled removal | 4.89× | 62 |
| sphere_still | Zero removal | 5.37× | 146 |
| sphere_still | Profiled removal | 5.63× | 18 |
| flat_still | Zero removal | 5.30× | 64 |
| flat_still | Profiled removal | 5.17× | 154 |

The fixed comparison used one native calculation per method and case, all 26/27 parameter columns and identical input arrays. All timing-boundary counts match. The measured ratios exclude compilation, input construction and evidence storage; they do not predict whole-fit runtime.

Twelve calls and 5,184,000,000 conservative packet/query work units were charged. Total elapsed time was 21.13 minutes on one numerical thread. No optimizers, observed inputs, original files or protected groups were used. The acceptance tolerance is unchanged.

The next performance step is to locate the derivative discrepancies in the saved matrices. A revised implementation would need separate qualification before any fitting change.

[Frozen plan](PLAN.md) · [Earlier small checks](../mixed-tangent-prototype/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
