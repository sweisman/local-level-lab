# Geographic rate-adapter qualification

**72/72 generated cases passed the frozen checks.** The declared generated calculation qualified.

**The hold rules are judged on numerical refinement; only linear points
must also pass the metre-level accuracy screen.** A hold-rule pass does
not mean its absolute errors are small.

Each case reconstructs a twenty-minute maneuvering trajectory from generated
angular rates and specific force at 300 Hz, then repeats at 600 Hz.
All three physical candidates, both latitude signs and both removal
assumptions are retained. Initial state and zero antenna lever arm are known
in these controls. Errors use each generating geometry in actual Cartesian
metres, projected onto its true local axes.

| Sampling hypothesis | Checks passed | Met accuracy screen | Accuracy required | Largest horizontal RMS at 300 Hz | Largest height RMS at 300 Hz |
|---|---:|---:|---|---:|---:|
| Hold previous sample | 24/24 | 0/24 | No | 587.29 m | 8.46757 m |
| Hold next sample | 24/24 | 0/24 | No | 587.296 m | 8.36037 m |
| Linear point samples | 24/24 | 24/24 | Yes | 0.0335567 m | 0.0281336 m |

The frozen linear-point screen requires horizontal and height RMS at most
1 m and maximum three-dimensional error at most 5 m. Refinement requires
the finer-grid maximum error to shrink by the predeclared factor, allowing
0.001 m for the numerical comparison. These are software targets, not
instrument specifications or calibrated uncertainty.

The run records 144 native propagations over 31.29 minutes. Sealed construction journals record 77,760,000 constructed intervals and 77,846,544 generated samples.
Saved-only verification checks all artifact hashes, error summaries, gate
labels, shared generated inputs, compiled source and main/custom charges.
It does not propagate again or generate new truth. Failures remain preserved.

This study reads no original recording and makes no Earth-model decision.
It does not identify the instrument’s actual sampling phase, averaging or
filtering. Receiver errors, antenna motion, uncertain initialization and
calibration still require qualification before an observed ESA comparison.
The version-1 zero-eligible inventory and confirmation reservation are unchanged.

[Frozen question and limits](PLAN.md) · [Implementation](IMPLEMENTATION.md) · [Earlier local checks](../esa-rate-qualification/INTERPRETATION.md) · [Motion limitations](../ESA_MOTION.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
