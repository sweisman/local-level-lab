# Withheld prediction errors and receiver-reported precision

This saved-data check uses the three recordings already selected for the retrospective prediction pilot. It ran no new model fits. Each setting chose a numerical start using the earlier training cost alone; later errors did not choose the start.

**Result:** all saved epochs matched that recording’s primary receiver precision report. Of 36 model, timing and processing settings, 28 had a numerically qualified start and eight did not. The receiver’s stated precision is its own estimate, not a measured truth error. Dividing prediction error by that estimate describes scale; it does not establish statistical significance.

| Model | Qualified / 12 | Passed earlier uncalibrated accuracy screen | Median later north / east / height RMS (m) | Median error / receiver-reported sigma, north / east / height |
|---|---:|---:|---:|---:|
| globe with specified field | 9 / 12 | 7 | 1.10 / 1.34 / 8.54 | 4.2 / 4.2 / 11.0 |
| globe with zero field | 9 / 12 | 0 | 305.17 / 391.37 / 7.24 | 611.3 / 871.5 / 10.8 |
| stationary disc | 10 / 12 | 0 | 148.72 / 566.43 / 35.75 | 350.6 / 1619.2 / 32.8 |

These are descriptive medians across different recordings and settings, including models that may be wrong. Individual settings and numerical abstentions remain in the verified report. The reported receiver precision does not include IMU, calibration, model or shared navigation errors. This study therefore makes no positive scientific decision and does not calibrate an absolute goodness-of-fit test.

The zero-fit study, exact selected starts, matched epochs, source hashes and recovery evidence are retained in the repository’s study archive. Re-run the auditor with `~/venv/bin/python -m lll.receiver_precision_holdout_audit`.
