# Apply the same absolute accuracy limits to 12 ESA windows

Use the four rolling cuts and the eight released turn and steady forecasts
from ESA development recording 187. Keep the same 120 later GPS reports
per window and both archived IMU error laws. Score the raw predicted paths.
Use the common receiver-coordinate conversion with the local scale at each
GPS position. Report north, east, horizontal and height RMS, peak horizontal
and absolute height error, and each failed limit.

Reuse the [existing ESA limits](ESA_400_120_MODEL_MATRIX_PLAN.md). Horizontal
RMS must be at most 10 m, height RMS at most 30 m, peak horizontal error at
most 50 m and peak absolute height error at most 150 m. Report the frequency
by window class, treating the two error laws as evaluations of the same data.
Keep the error laws separate when their flags differ.

Verify the selected forecasts, receiver clocks and prior scores. Preparation
may read the one previously opened GPS receiver file once, for exactly the
960 later positions required by the eight turn and steady windows. The
four rolling cuts use their archived errors. Freeze these inputs and use
twelve identities, 24 charged arithmetic checks, one worker and one thread
with a 90-second cooperative limit. Use zero navigation fits, native calls,
IMU file reads or reserved-flight reads. Preserve every earlier result.

Passing this descriptive test means the predicted and reported positions
are close on that window. It does not calibrate aircraft uncertainty or
count the twelve windows as independent flights.
