# Calibration boundaries and fit quality

**The complete first-pass comparisons favor globe in 12 stretches and flat in none; all 12 also favor rotation.** This audit explains calibration limits and the fit-quality information already saved. It does not change those comparisons.

It reads 318 original fits and 12 matched solver-trial fits. No original IMU log was opened, no integration was evaluated, and no optimization was started. Baseline and trial are kept separate; repeats are not new independent observations.

An **IMU (inertial measurement unit)** measures turning and acceleration. These are survey-grade instruments. Published performance information supports continued modeling; exact device characterization remains parallel work, not a prerequisite for this audit.

## What the solver trial accomplished

The revised solver completed 10/12 fits, compared with 11/12 in the saved baseline. The completed control still favors globe and then rotation. The diagnostic stretch remains unfinished. The trial did not improve completion and does not justify a rollout to the remaining stretches. [Original matched evidence](../ilvis0-solver-trial-20261010/RESULTS.md).

## Signed parameter boundaries

A parameter is counted at a limit using the original rule: its normalized absolute value is at least 0.999. Lower and upper signs refer to decoded sensor axes and the fitted correction parameters, not geographic north/down. A gain is a fractional correction: corrected increments are divided by one plus that gain after subtracting the fitted offset times the integration interval. A fitted offset is not a measurement of time-varying drift.

| Parameter | Lower limit | Upper limit | Interior | Total at a limit |
|---|---:|---:|---:|---:|
| gyro_gain_z | 258 | 46 | 14 | 304/318 |
| gyro_bias_z | 225 | 69 | 24 | 294/318 |
| earth_removal | 108 | 14 | 37 | 122/159 |
| gyro_gain_x | 11 | 214 | 93 | 225/318 |
| gravity_delta | 198 | 26 | 94 | 224/318 |
| gyro_gain_y | 76 | 141 | 101 | 217/318 |
| lever_x | 121 | 88 | 109 | 209/318 |
| gyro_bias_x | 192 | 12 | 114 | 204/318 |
| accel_gain_y | 134 | 54 | 130 | 188/318 |
| accel_gain_x | 83 | 100 | 135 | 183/318 |
| accel_bias_x | 163 | 16 | 139 | 179/318 |
| lever_y | 58 | 121 | 139 | 179/318 |

Z-axis gyro gain and offset reach a limit together in **282/318 fits**.

| Model / processing case | Z gain lower / upper | Z offset lower / upper | Both at a limit |
|---|---:|---:|---:|
| sphere_rotating / bias1_unsubtracted | 26 / 20 | 21 / 21 | 35/53 |
| sphere_still / bias1_unsubtracted | 52 / 1 | 48 / 5 | 53/53 |
| flat_still / bias1_unsubtracted | 53 / 0 | 48 / 5 | 53/53 |
| sphere_rotating / bias1_profiled_removal | 22 / 24 | 15 / 25 | 35/53 |
| sphere_still / bias1_profiled_removal | 52 / 1 | 48 / 5 | 53/53 |
| flat_still / bias1_profiled_removal | 53 / 0 | 45 / 8 | 53/53 |

The paired signs are in [Z-axis estimates](z-axis-pairs.csv). [Every parameter estimate](parameter-estimates.csv) preserves physical values, units, limits and distance to a boundary. [Boundary summaries](boundary-summary.csv) separate model, processing case and numerical completion. These numbers identify where the model needs scrutiny; they do not establish that a sensor physically had that error.

## Parameter associations and weak directions

The correlations below compare saved Z gain/offset estimates across stretches, within the same model and processing case. They are descriptive, not within-fit uncertainties or independent-flight significance tests. Values counted at a boundary are snapped to that boundary for correlations, avoiding false rankings from floating-point jitter.

| Model / processing case | Fits | Z gain/offset rank correlation |
|---|---:|---:|
| flat_still / bias1_profiled_removal | 53 | Not estimable |
| flat_still / bias1_unsubtracted | 53 | Not estimable |
| sphere_rotating / bias1_profiled_removal | 53 | 0.13 |
| sphere_rotating / bias1_unsubtracted | 53 | 0.173 |
| sphere_still / bias1_profiled_removal | 53 | -0.0448 |
| sphere_still / bias1_unsubtracted | 53 | -0.0448 |

[All parameter-pair correlations](parameter-correlations.csv) also separate completed fits from all saved estimates. The trial supplies its three weakest saved singular-vector directions per fit in [local directions](weak-directions.csv). Their coefficients use normalized parameter coordinates. These unconstrained local directions can be blocked by active bounds and are not covariance estimates or proof of global ambiguity. The original 318 fits did not save their singular vectors.

Across the 12 trial fits, the leading coordinates in the three weakest directions are counted below. Repeated weak Z-axis directions point to calibration trade-offs worth testing, rather than demonstrating large physical instrument errors.

| Leading coordinate | Saved weak directions |
|---|---:|
| gravity_delta | 12 |
| gyro_bias_z | 12 |
| gyro_gain_z | 12 |

## Absolute fit-quality information available now

Whitened RMS is the square root of the saved weighted sum of squared errors divided by **three times the fitted receiver-epoch count**. It describes errors relative to the assumed covariance; it is not reduced chi-square, a p-value, or a calibrated pass/fail criterion. Every saved section count and physical RMS is checked against the whole-stretch record before reporting. Horizontal RMS combines north/east axes. Physical metres use each candidate's declared coordinate metric, as in the original analysis. Coordinate-ablation checks remain separate work.

| Completed baseline fits | Fits | Median whitened RMS | Median horizontal RMS (m) | Median vertical RMS (m) |
|---|---:|---:|---:|---:|
| sphere_rotating | 43 | 0.0343 | 0.072 | 0.425 |
| sphere_still | 73 | 2.86 | 29 | 1.64 |
| flat_still | 72 | 4.07 | 45.3 | 1.51 |

The table above includes different completed subsets for the three models. **The matched table below uses the same 12 fully resolved stretches under both processing cases for every model.**

| Matched complete comparisons | Fits | Median whitened RMS | Median horizontal RMS (m) | Median vertical RMS (m) |
|---|---:|---:|---:|---:|
| sphere_rotating | 24 | 0.0324 | 0.0682 | 0.393 |
| sphere_still | 24 | 2.86 | 29.5 | 1.76 |
| flat_still | 24 | 4.25 | 47.1 | 2.13 |

For the 12 fully resolved stretches, the 24 preferred rotating-globe fits (two processing cases per stretch) have median horizontal RMS **0.0682 m** and vertical RMS **0.393 m**. Their whitened RMS spans 0.0221–0.0969. These residuals are concrete fit-quality evidence. Whitened RMS far below one means the remaining errors are small relative to the assumed covariance; it does not verify that covariance or its independence assumptions. Judging the error distribution and prediction reliability requires the missing checks below.

[Per-fit adequacy ledger](fit-adequacy.csv) includes all fits, receiver counts, physical RMS, primary and conservative-covariance whitened RMS, clock sensitivity and fixed-parameter section counts. Unfinished fit costs are retained as diagnostics, not used to rank models. Lower residuals under a more generous covariance are not a refit.

## What cannot be recovered from these saved summaries

- No epoch-level residual vectors were saved, so quantiles, outliers, temporal autocorrelation and residual dependence on speed/latitude/maneuvers cannot be reconstructed from RMS.
- Fixed-parameter sections use observations that already informed the whole fit; they are not held-out predictions.
- No documented temperature channel is available in these saved fit records. Elapsed time and flight motion are not measurements of sensor temperature.
- No independently validated absolute-fit threshold exists yet. All ledger entries therefore say adequacy is not calibrated; that does not erase the relative model findings.

## Next bounded work

Inspect the signed Z gain/offset behavior together with integration timing and the correction convention before adding calibration freedom. Save epoch-level primary and conservative residuals in a separately identified diagnostic pass if approved. That requires new native predictions and a finite numerical scope, even though it need not refit. Then specify matched timing/calibration alternatives and genuine blocked or separate-flight prediction checks before observed starts. Apply them equally to all three models; do not tune limits to increase globe support.

See the [analysis roadmap](../ANALYSIS_ROADMAP.md). Device documentation can improve assumptions in parallel; the numerical and saved-data work does not wait for it.

## Reproduce

From the repository root:

```sh
env PYTHONPATH=analysis ~/venv/bin/python docs/ilvis0-calibration-audit-20261010/build_report.py
```

The builder verifies both publications and their hashes before analysis. Its receipt hashes inputs, reporting sources and outputs. CSV uses LF line endings. It never imports a fitting kernel, changes selection or alters a scientific decision.
