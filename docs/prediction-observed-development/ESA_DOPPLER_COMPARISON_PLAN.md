# Compare ESA Doppler velocities and integrated motion with the export

Use the sealed GPS and GLONASS velocity paths and the original 520
matched receiver reports from development recording 187. Use the
export's latitude and longitude to express each velocity difference
in one common local frame. Report signed means, RMS and correlations
at 1, 5, 20 and 60 report lags, separately for the earlier 400 and
later 120 reports. Include the GPS-minus-GLONASS series.

Separately integrate each sealed half-second Earth-fixed velocity
path by trapezoids. For the earlier interval anchor at report 0.
For the later interval anchor at the final earlier report, index 399.
Do not fit a position offset, remove velocity bias, or correct the
path using later reports. Report the integrated path offset at each
matched receiver position and the endpoint offset. The fixed match
uses the receiver clock correction already checked against the
export. Integrate relative to the nominal half-second clock.

Bind the sealed inputs, exact source and numerical environment
first. Use one numerical thread. Allow zero new fits or forecast
propagations. Keep the seven reserved flight groups closed. This
check compares how motion was reconstructed on one development
flight. Shared measurements prevent it from qualifying absolute
receiver accuracy or empirical flight-level coverage.

[Doppler reconstruction plan](ESA_DOPPLER_VELOCITY_PLAN.md)
