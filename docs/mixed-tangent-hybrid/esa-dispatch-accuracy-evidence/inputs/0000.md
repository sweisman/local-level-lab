# Check the saved ESA forecasts against later positions

The [solver comparison](OBSERVED_DISPATCH_FRESH_RESULT.md) saved 32 paths
from recording 187. Its fits used 800 earlier receiver positions and the times
of 400 later observations. This follow-up scores those paths against the
later positions. It uses one development flight and requires no new fits.

For each of the eight settings and each solver, select the start with the
smallest earlier fit cost. Use start 0 for an exact tie. Write down all 16
selections and the hashes of all 32 paths before decoding later positions.
Score the other starts too so readers can see how much the choice mattered.

Use receiver rows 13098 through 13896, every other row, counting from zero.
Match their times exactly. Use the first 120 and 240 positions to show how
errors develop, and all 400 for the primary result. The three horizons share
observations. Use the [existing accuracy limits](../prediction-observed-development/ESA_ABSOLUTE_ACCURACY_PLAN.md)
of 10 m horizontal RMS, 30 m height RMS, 50 m peak horizontal error and
150 m peak height error. The limits are descriptive. The fit settings
are two globe models, two processing assumptions and two receiver error
policies. This check supports no shape or background-field decision.

Use one worker, one numerical thread, a 120-second execution allowance and
32 path scores. Preparation verifies the release, hashes one receiver export,
and decodes only the 400 later rows. The worker opens the frozen forecasts and
matched receiver rows. No step opens original inertial files or reserved flights.
The shared recovery rule covers technical interruption. A completed result is
sealed with all path scores.
