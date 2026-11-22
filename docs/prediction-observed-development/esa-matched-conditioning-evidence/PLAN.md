# Compare raw and earlier-conditioned predictions on identical GPS support

Start with the [twelve-window raw accuracy audit](ESA_RAW_ACCURACY_RESULT.md).
Reuse its eight matched turn and steady results unchanged. For rolling
cuts at 200, 400, 600 and 800 GPS reports, compare the existing raw paths
and previously sealed forecasts conditioned on earlier GPS residuals.
Use the same 120 later positions, both inertial error laws and the same
fixed RMS and peak limits throughout.

Accept an adjusted path only when its seal and scoring receipt identify
the same earlier fit, instrument error law, forecast times and receiver
source as the raw path. Check the link to the exact raw path at the
800-report cut separately. Carry any unmatched law or path as unavailable.
Keep all eight rolling cut-law identities in the denominator. Report raw
and adjusted errors and changes in the accuracy flags separately. Apply
the existing screen to the recorded paths, without transferring a pass
from the other law or using later residuals to change a forecast.

The preflight found an exactly matching raw path and clock for the
[800-report adjusted forecast](CONDITIONAL_FORECAST_RESULT.md) under the
increment law. Its raw path differs from the point-law path. Treat the
point-law comparison as unavailable unless a separately sealed match
exists.

Use at most eight charged score comparisons on one thread, with a
90-second cooperative limit. Use no new fits, integration, original-file
reads or reserved-flight reads. This is an error check on one development
flight. It leaves the aircraft uncertainty and flight-level decision gates
open.
