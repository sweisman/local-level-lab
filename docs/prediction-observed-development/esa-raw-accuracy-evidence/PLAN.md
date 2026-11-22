# Check all twelve ESA windows on the raw forecast scale

The first [accuracy audit](ESA_ABSOLUTE_ACCURACY_RESULT.md) scored the
released turn and steady paths after adjustment using earlier GPS errors.
Its four rolling paths were raw. Preserve those scores and evaluate the
archived raw paths for the same eight turn and steady forecasts. Use the
same chosen starts, 120 later receiver positions and four accuracy limits.
Reuse the completed raw scores at the four rolling cuts.

For each turn and steady window, check both inertial error laws and report
the raw and adjusted horizontal and height RMS, their peak errors and the
four limit flags. The archived raw path must be the full prediction from
the same earlier fit as the released adjusted path. It must share the
original receiver clock and contain no later GPS position corrections.

Use eight task identities, 16 charged checks, one worker and one thread
with a 90-second cooperative limit. Reuse the first audit's frozen GPS
positions. Use zero new fits, native calls, original-file reads or
reserved-flight reads. These comparisons share one development flight
and leave aircraft uncertainty uncalibrated.
