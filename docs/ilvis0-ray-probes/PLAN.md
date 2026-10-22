# Smaller calibration rays in the complete nonlinear model

The earlier twelve linear-extreme proposals all failed nonlinear training.
This study checks whether smaller versions can fit training positions yet
separate later predictions. It uses the same two generated specified-field
histories and both processing assumptions, not aircraft or protected ESA data.

Keep all twelve saved proposal directions, all 27 parameters, the original
physical limits and ±1-second clock support. For each direction use only the
292 saved training epochs, its zero-reference Jacobian and its earlier nonlinear
endpoint. Write L for the linear training change and Q for the remaining
endpoint change. Choose a dyadic scale by 48 fixed bisections, requiring
`max|L|*a + max|Q|*a² <= 0.75 m`. This quadratic expression is a proposal
heuristic, not an enclosure of the nonlinear trajectory.

Save each represented scaled point before one new full nonlinear query at all
293 original times, including the future endpoint at 438 seconds. No new
outcome may change that point or cause a retry. The actual training-feasibility
criterion remains ±1 metre on every coordinate at all 292 earlier epochs.
Neither the future outcome nor its ranking determines feasibility.

| Resource | Per identity | Maximum total |
|---|---:|---:|
| Started identities | 1 | 12 |
| Native batches | 1 | 12 |
| Queried epochs | 293 | 3,516 |
| Conservatively charged packet visits | 28,128,000 | 337,536,000 |
| Proposal / search steps | 1 / 48 | 12 / 576 |
| Exact training column products | 23,652 | 283,824 |

Reserve one numerical thread and two for the running long-record study, with
a ten-minute cooperative ceiling. Freeze source, generated-input references,
environment, compiler and counts before launch. No optimizer starts, original
aircraft reads, process signals, retries or allowance expansion.

Report all outcomes. Among numerically feasible points and the zero reference,
report the spread of future predictions under each processing assumption,
beside the unchanged 20/20/50-metre width targets. This is a numerical ambiguity
diagnostic, not a complete uncertainty enclosure or a proof of native
floating-point execution error. No feasible sampled separation would prove
unique prediction either. The original long study has perturbed training data;
this separate zero-reference fixture must not be described as its result.
