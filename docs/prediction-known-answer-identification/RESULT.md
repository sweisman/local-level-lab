# Known-answer error-law trial

**400 of 400 generated histories completed.** This is a software
diagnostic, not a flight result or a calibrated detection.

| Generating error law | Sampling | Provisional single law | Correct | Wrong | Abstain | Oracle 95% coverage |
|---|---:|---:|---:|---:|---:|---:|
| reference | 1 s | 8/100 | 8 | 0 | 92 | 947/1,000 |
| reference | 10 s | 55/100 | 54 | 1 | 45 | 932/1,000 |
| persistent | 1 s | 36/100 | 35 | 1 | 64 | 939/1,000 |
| persistent | 10 s | 67/100 | 64 | 3 | 33 | 946/1,000 |

Across all cases, 166 histories selected one law, 234 abstained and 5 selected the wrong candidate. The correctly supplied law covered 3764/4,000 withheld receiver epochs with nominal 95% intervals. Local
training-information rank was three in every task, yet individual
short histories often could not choose one law. This is why rank
alone cannot qualify uncertainty.

The first allowance completed every calculation but failed its
result-schema gate. Its 404 charged operations remain preserved.
The corrected allowance separately completed and verified all four
tasks. Its 404 charged operations and 1,624 steps are sealed.

This trial learns only among three fixed error laws in a simplified
linear model. It does not assess nonlinear aircraft fitting, actual
sensor errors, receiver-coordinate adequacy or flight-level coverage.
The next gate is a full known-answer aircraft prediction test.

[Method and finite limits](PLAN.md) · [Correction receipt](PLAN_V2.md) · [Verified numbers](verified-report.json).
