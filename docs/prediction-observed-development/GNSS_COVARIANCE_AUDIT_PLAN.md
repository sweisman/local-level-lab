# Receiver covariance audit on the opened training interval

The GNSS-only PPP export reports north/east/up position and velocity
covariance fields. This diagnostic asks whether those printed matrices are
algebraically usable and how the already reported position-derivative minus
velocity contrast depends on time. It cannot measure absolute receiver error:
position and velocity come from one PPP solution, and cross-time and
position-velocity covariance are not supplied.

Verify the original recording-187 GNSS export against its published SHA-256.
Open the existing sealed 400-report earlier fit input, match each report to
the original export by GPS time, sequence and coordinates, and stop parsing
immediately after the last matched training report. Do not decode any of the
120 withheld reports or open the seven protected ESA flight groups. Preserve
the original six covariance values and their header order. Assemble symmetric
north/east/up matrices from NN, EE, HH, EN, NH and EH and count negative
eigenvalues, allowing only rounding-scale negatives. Report median square
roots of printed diagonal fields. The source header labels position
covariance in m² and velocity covariance in m²/s²; those units do not
establish empirical coverage.

Independently recompute centered WGS84 position derivatives on the 400
training reports. Require their mean, RMS and 95th-percentile contrast to
reproduce the existing saved consistency report. Report lag-1, 2, 5 and 10
correlations of that contrast for each axis. Report raw summaries rather than
a normalized significance test: the missing cross-time and cross-field
covariance means such a test would be unjustified. The [Waypoint output
documentation](https://docs.novatel.com/Waypoint/Content/Appendix/Output_Variables.htm)
describes local-level position/velocity covariance variables but does not
establish empirical coverage for this specific PPP export.

This is a finite read-only audit, with one original export verified and
training records decoded, zero IMU samples, zero model fits and zero
protected-group reads. It may reject a naive independent-epoch receiver law;
it cannot qualify an effective aircraft prediction-error envelope by itself.
