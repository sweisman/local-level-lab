# Rebuild static references from compact verified inputs

Use the same six generated long-history cases, covering all three physical
candidates and both processing assumptions. Verify the parent completion,
manifest, case, saved reference and training-region hashes before extracting
the configuration, first velocity increment and first sample interval.

Reconstruct each full calibration reference and require exact agreement with
its saved report, including its source binding, coefficients and normalization
caps. Do not load a trajectory history in the worker or integrate any motion.
Keep all 27 physical and 24 shared coordinates available for the later coupling
diagnostic; this check does not itself constrain or qualify predictions.

Limits: six identities, one reference reconstruction per identity, one numerical
thread, 120 cooperative seconds and no retries. Charge the six reconstructions
before execution in indexed journals. There are no LP proposals, support solves,
trajectory bounds, native calls, aircraft reads or optimizer starts.

Passing establishes compatibility of the compact inputs with the saved static
references. It does not establish a physical error law, uncertainty coverage or
recording-length prediction usefulness.
