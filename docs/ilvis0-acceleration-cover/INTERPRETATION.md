# Common acceleration: complete comparison

All **48 sectors pass correctness**. All six cases also pass the unchanged tenfold width-reduction target against the original broad-box baseline. Complete union widths range from **0.061 to 0.358 m** across axes and cases.

| Candidate / processing | Complete | North / east / height union width (m) | Ratio to original broad-box widths |
|---|---|---:|---:|
| Globe + specified field, zero removal | Yes | 0.277, 0.350, 0.194 | 0.000361, 0.000596, 0.000378 |
| Globe + specified field, profiled removal | Yes | 0.286, 0.358, 0.202 | 0.000371, 0.000608, 0.000394 |
| Globe, zero field, zero removal | Yes | 0.225, 0.236, 0.138 | 0.000293, 0.000402, 0.000269 |
| Globe, zero field, profiled removal | Yes | 0.243, 0.253, 0.156 | 0.000316, 0.00043, 0.000304 |
| Flat disc, zero removal | Yes | 0.183, 0.061, 0.123 | 0.000238, 0.000354, 0.000241 |
| Flat disc, profiled removal | Yes | 0.205, 0.068, 0.145 | 0.000266, 0.000391, 0.000284 |

These are conservative calculated ranges at **1.8 seconds in generated data**, not measured aircraft errors, calibrated prediction intervals or a new model preference. All original physical models, 27 calibration directions and bounds remain. Fifteen auxiliary coordinates preserve common errors across measurement times; they are not new independent physical choices at each epoch.

The study charged 144 native evaluations and completed in 1432.6 seconds. Source/input/environment freezes, native values/Jacobians, training inequalities and future support certificates remain available. This report verifies the published hashes and reconciles every complete union against its sectors, without numerical integration, optimization or original-file reads.

Longer recording-scale usefulness, whole-program floating-point treatment, actual receiver-error adequacy and independent confirmation remain separate gates. No protected ESA outcomes are used. The 53-stretch empirical comparison is unchanged; scientific decisions remain abstention.

[All saved results](README.md) · [Frozen method](PLAN.md) · [Native qualification](../ilvis0-acceleration-native-controls/INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
