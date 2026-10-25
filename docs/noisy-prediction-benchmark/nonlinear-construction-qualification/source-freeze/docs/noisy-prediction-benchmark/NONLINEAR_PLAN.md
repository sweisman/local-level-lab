# Does the noise approximation survive nonlinear motion?

The completed benchmark predicts an error scale of about 34 m over the later
part of a twenty-minute generated recording. This is a calculation from an
assumed noise law. The next check compares that approximation with integrations
of actual generated sensor errors, without fitting any calibration parameters.

Reuse the same four settings, known starting state, known calibration, motion,
receiver law and chronological split. Keep future receiver errors out of the
physical-position target. The nominal future geometry remains an explicit extra
piece of knowledge in this software check; it cannot enter aircraft prediction.

For each setting use 16 predetermined seeds, 26102500 through 26102515. Draw
sensor and earlier receiver errors using the existing independent noise
generators. Integrate each error path at +1, -1, +1/2 and -1/2 amplitude. These
four paths are one matched control, not four independent observations. Report
the part that fails to reverse sign and the change in response when amplitude
is halved. Both include the earlier-only conditional correction. Compare each
coordinate with the larger of 1 mm and 1% of its predicted standard deviation.
Freeze these limits before executing; retain every failed setting and seed.

This is a finite test of the linear approximation at the stated settings. Passing
does not prove a global remainder bound, calibrated coverage, adequacy of the
archive noise law, or uncertainty after fitting unknown calibration. The fixed
10 m horizontal / 30 m height screen and all earlier results stay unchanged.

Implementation uses `lll.noise_nonlinearity` for draws, known-calibration
propagation, chronological conditioning and matched summaries. Reuse
`lll.generated_noise_benchmark`, `lll.measurement_noise`, the existing native
value kernel, and `lll.studies` for execution. Do not copy a worker tree.

First test the shared operations without native compilation. Then freeze a
separate two-second native qualification for both input laws, comparing the
known-calibration wrapper with the existing independent wider-tangent reference.
Each case allows 700 native calls, 10,000 packet steps and 40,000 packet-query
visits, 610 generated samples, 600 constructed intervals and 20,000 normal
variates. The two existing native libraries and one scalar-value library are
allowed; one numerical thread reserves two threads for the existing test job.
The cooperative allowance is three minutes, with no retries or optimizer starts.

A later four-setting run needs its own qualified lifecycle and separate finite
freeze. This plan does not itself launch the longer calculation. No original
recording or reserved ESA group is read.
