# Receiver shift needed to tie sealed forecast scores

Use only the sealed 400-training/120-later ESA development matrix, its saved
parent receiver cut and the completed alternate-PPP score receipt. Consider
the two settings in which all three required model fits passed the original
numerical checks. Read sealed future forecasts; run no fit or native forecast.
Keep the original `air1` receiver-coordinate metric fixed on the 120 later
epochs. Reproduce the saved model scores exactly before calculating margins.

For each preferred specified-field globe forecast against the zero-field
globe and flat-disc forecast, calculate the smallest arbitrary 120-by-3
receiver-position perturbation that would make their **fixed** Euclidean
sum-of-squares scores tie. Also calculate the smallest *single constant*
north/east/up offset applied to every later epoch that makes them tie. Report
these as per-epoch RMS displacement and constant-offset magnitude, with
horizontal-only variants. Verify the formulas against an exact known-answer
case and by applying the computed shift to obtain a tie.

This is a diagnostic sensitivity bound, not a receiver error estimate or a
calibrated model test. Forecasts and the local coordinate metric are held
fixed. Changing coordinates, reestimating calibration or accounting for
shared receiver error may change the answer. The 120-epoch horizon came from
development work on this one flight. The seven reserved groups stay closed.
