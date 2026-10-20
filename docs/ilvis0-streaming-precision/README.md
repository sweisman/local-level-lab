# Long-record streaming and native arithmetic

6/6 controls pass; state: complete.

The reference controls compare the unchanged whole-array kernels with chunked predictions. Exact-pose errors remain separate from agreement between the calculations.

| Case | Mode | Packets | Streaming − reference / exact target | Streaming exact-pose error | Reference exact-pose error |
|---|---|---:|---:|---:|---:|
| reference | Value | 120,000 | 0 m | 3.4831937e-06 m | 3.4831937e-06 m |
| reference | 27-column tangent | 120,000 | 0 m | 3.4831937e-06 m | 3.4831937e-06 m |
| reference | Value | 480,000 | 0 m | 0.00022283864 m | 0.00022283864 m |
| reference | 27-column tangent | 480,000 | 0 m | 0.00022283864 m | 0.00022283864 m |
| exact-pose | Value | 480,000 | 0 m | 0 m | 0 m |
| exact-pose | 27-column tangent | 480,000 | 0 m | 0 m | 0 m |

The exact-pose controls use zero angular increments and exactly representable periods/gravity. The reference cases retain the earlier nominal-300-Hz specified-field input. The first study’s absolute-pose failure is preserved and is not relabeled by a successful equivalence comparison.

| Case | Mode | Runtime, streamed | Traced working peak | Native state |
|---|---|---:|---:|---:|
| reference | Value | 2.23 s | 0.418 MiB | 560 bytes |
| reference | 27-column tangent | 5.56 s | 0.370 MiB | 14,168 bytes |
| reference | Value | 8.66 s | 0.629 MiB | 560 bytes |
| reference | 27-column tangent | 23.61 s | 0.594 MiB | 14,168 bytes |
| exact-pose | Value | 8.97 s | 0.527 MiB | 560 bytes |
| exact-pose | 27-column tangent | 22.12 s | 0.572 MiB | 14,168 bytes |

Reference arrays/compiler/shared-library storage are outside the traced streamed working allocation. Predicted observations and derivatives are compared and discarded one block at a time. These generated controls do not establish observational accuracy, global rounding bounds or calibrated uncertainty.

Charged 2,116 calls and 3,360,000 packet visits in 94.09 seconds; zero archive fits.

[Frozen plan](PLAN.md) · [First qualification and retained failure](../ilvis0-streaming-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
