# Training and prediction with both working error cases

**48/48 generated fits pass the frozen checks.** The weighted calculation qualifies.

Both receiver-error cases use the same common fitting/forecast pipeline
planned for the observed ESA pilot. Calibration uses earlier positions only;
later positions are opened after the continuous forecast is saved.
The examples include turns, climbs and sensor/calibration errors, with no
random measurement noise. They are software controls, not ESA observations.

| Working error case | Generating geometry | Passed | Converged | Largest later spatial error |
|---|---|---:|---:|---:|
| reported-short-v1 | Globe with specified field | 8/8 | 8/8 | 2.71198e-05 m |
| reported-short-v1 | Globe with zero field | 8/8 | 8/8 | 2.73846e-05 m |
| reported-short-v1 | Tested disc | 8/8 | 8/8 | 7.62234e-05 m |
| reported-persistent-v1 | Globe with specified field | 8/8 | 8/8 | 2.00628e-05 m |
| reported-persistent-v1 | Globe with zero field | 8/8 | 8/8 | 2.16836e-05 m |
| reported-persistent-v1 | Tested disc | 8/8 | 8/8 | 6.82426e-05 m |

Every pass requires numerical completion, every nuisance column, training
and later horizontal/height RMS at most 0.1 m, and maximum spatial error
at most 0.5 m. Failed or unfinished cases retain their original labels.
No recovery of unique calibration or actual instrument precision is claimed.

The study used 490 native calculations in 5.01 minutes.
Saved-only verification reconciles original generated arrays, training
prefixes, earlier-only weights, compiled sources, independent Cartesian
position errors and all charged work. It performs no new fit or propagation.

Observed ESA fitting still requires its separate finite pilot definition.
The actual error model is uncalibrated, and seven confirmation groups
remain protected. The NASA findings are unchanged.

[Frozen question and allowance](PLAN.md) · [Prepared interval](../esa-development-pilot-preparation/README.md) · [Roadmap](../ANALYSIS_ROADMAP.md)
