# The first integrated candidate does not pass the full gate

**18/24 controls passed.** All six broad-domain cases stopped at the initial
source's unchanged nonlinear-cap check. The study is complete and will not be
retried. It charged 60 native evaluations, 348 complete bounds and 30,144 bound
steps in 136.30 seconds. Failed attempts and unused allowance remain preserved.

The successful controls retain the reference centers and all 51 columns. This
partial result does not qualify the candidate or permit a prediction comparison.
No aircraft fitting occurred.

The [post-run cap diagnosis](CAP_DIAGNOSIS.md) finds that the new proof used a
symmetric box larger than the original asymmetric calibration domain. Computing
the proof on the actual domain fits the original cap in all six failed cases.
The cap and physical bounds remain unchanged. A separate revised candidate
must still pass the complete native matrix.

[Evidence](README.md) · [Fixed scope](PLAN.md) · [Cap diagnosis](CAP_DIAGNOSIS.md).
