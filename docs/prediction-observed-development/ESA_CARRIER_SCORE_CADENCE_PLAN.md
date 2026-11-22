# Which carrier errors can a ground receiver check?

Use the frozen signed carrier weights for the two-minute ESA development
comparison. A ground receiver reports carrier changes between its own samples.
Within each interval, project the half-second score weights onto the range
totals that can be formed from satellite signals continuous in both streams.
Remove a common clock term separately in each interval. Use only exact pairs
and sum their ranges without inventing intermediate ground measurements.

Compare three settings. The first uses the actual 30-second ground intervals
and their common satellites. The second assumes ideal one-second ground
coverage on the full two-minute grid with all eligible aircraft satellites.
The third uses ideal 30-second sampling over the full window, to distinguish
lost coverage from cadence. Report the norm of the visible and unobserved
score weights in each. A norm fraction describes the geometry of the score
and supplies no estimate of the share of actual error that was measured.

For the actual 30-second data, project the saved signed ground residual
onto the visible part of the score. Also report the score equivalent after
applying the multiplier trained on earlier disjoint intervals. This assumes
the corresponding satellite term transfers to the aircraft. It estimates
neither the true aircraft position error nor the unobserved part of the score.

The freeze uses signed results from completed studies. One task runs on one
thread with a 180-second cooperative cap and four charged operations, one to
bind inputs and one for each cadence. It runs zero fits and reads no reserved
flight. The existing verified interruption recovery applies.
