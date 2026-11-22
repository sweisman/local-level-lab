# Does an earlier Qaqortoq correction help later?

Use the same aircraft path, final satellite products and original 1 Hz Qaqortoq
record as in the fixed score comparison. Estimate one least-squares multiplier
for the clock-centered ground residual using only the earlier 335 seconds on
flight 187. Use integer GPS seconds 388215 through 388550 and exclude the known
aircraft clock step. The later score window begins at GPS second 388614 and
shares no observations with estimation. Its observations and original scores
were already available, so this is a chronological development check.

Keep the accepted GPS `L1C` and `L2W` arcs and require five or more common
satellites. Compare the original residual, full ground subtraction and the
earlier multiplier held fixed. Report the later residual RMS, the signed change
in the saved carrier score measure and how many intervals entered the analysis.
Leave unmatched intervals unused and preserve the exact signed rows.

Allow one task on one numerical thread, one setup, 335 earlier interval
calculations and one summary of the 120 later intervals. The cooperative time
cap is 180 seconds. No receiver path or model is re-fit. Technical recovery
uses the qualified finite procedure. The study uses no reserved flight.
