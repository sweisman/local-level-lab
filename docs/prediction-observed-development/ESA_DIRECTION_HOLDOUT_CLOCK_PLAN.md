# Align the second-leg receiver queries at whole seconds

The [alternate receiver test](ESA_DIRECTION_HOLDOUT_RECEIVER_RESULT.md)
found no matches for the four second-leg windows at the original
half-second query times. Keep those four 420-second cells and take the
previous 2 Hz report for every query. Keep the first-leg scores and the
original second-leg results as separate evidence. The clock change uses
the known receiver schedules and leaves the original cell selection in
place.

Check all four shifted primary schedules and both alternate sources.
Require the primary 400 reports per cell to move earlier by 0.5 seconds
within a 2 ms tolerance and to lie on whole seconds within 2 ms. Keep
at least 20 original receiver reports between each query set and the
cell edges. Apply the same 2 ms matching tolerance to the ordered,
original alternate reports without interpolation. If any export has
missing coverage, record the gap and withhold that cell from the
follow-up comparison.

On complete cells, seal the three receiver inputs and the three original
field-state predictions from the primary receiver. Keep the two matched
differentiation methods and both time-averaging widths. The matched
receiver records include their original timestamps and source hashes.
A later stage can evaluate the same continuous field ranges after reading
the IMU at the shifted times. That comparison will still use the same
four underlying flight cells.

Allow one clock-and-prediction task. Use one scan over at most 64,080
primary reports, one hash and parser pass per audited alternate export,
and up to eight paired-method forecast operations across the four cells
and two averaging widths. Use one numerical thread and a 90-second
ceiling. Read only the three previously opened receiver exports. Run no
fits or inertial reads and keep the seven reserved groups unopened.
