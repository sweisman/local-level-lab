# Rescore the sealed ESA forecasts against GLONASS

Use the already sealed GLONASS paths, the same 520 GPS-time matches,
and the same six forecasts from the two complete earlier comparisons.
Require both GLONASS methods to have a solution at every matched epoch.
Report GLONASS-minus-export component RMS and signed means on the
earlier 400 and later 120 rows. Rescore each fixed forecast on the
same 120 later rows using each GLONASS path, in exact Cartesian distance
resolved into the local axes. Apply the same descriptive accuracy
limits and shape-before-field ranking. Keep both incomplete settings
unresolved. Do not interpolate, fit a new offset or choose a preferred
position series from the observed outcome.

Bind the exact forecast, source, inputs and environment before scoring.
Allow no new fits or forecast propagations. Run on one numerical thread.
All reserved ESA flight groups stay closed. GLONASS and GPS use
different satellites and a shared aircraft antenna. This comparison
does not establish absolute accuracy or independence across flights.

[GLONASS reconstruction](ESA_GLONASS_CODE_PLAN.md) ·
[GPS comparison](ESA_RINEX_CODE_COMPARISON_RESULT.md)
