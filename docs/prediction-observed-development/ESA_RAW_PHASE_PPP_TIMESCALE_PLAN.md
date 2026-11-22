# Compare the two GPS measurements over longer intervals

The [one-second comparison](ESA_RAW_PHASE_PPP_CLOSURE_RESULT.md) found
some directional agreement between exported position changes and raw
carrier changes. The full projected positions were no better than
predicting zero difference in the later portion. Test whether the
measurements agree better over longer intervals.

Use every archived interval from the finished comparison. In the
earlier and later portions separately, start at the first interval and
take consecutive nonoverlapping blocks of 1, 4, 16 and 60 seconds.
Retain each full block. Mark blocks that cross the original excluded
clock step or lack at least five satellites present throughout. Keep
the undeclared trailing partial blocks out of the totals and report
their lengths.

For every block and satellite, sum the recorded and projected signed
range changes over the same steps. Remove one median per summed
contrast using the satellites present throughout. Compare RMS and
squared error with the same zero-difference baseline. Report all three
pairs, both portions, every duration, and the number of retained blocks.
Record the signed correlation across the centered satellite contrasts.
No scale, lag or window selection is fitted from the comparisons.

Freeze the previous result and exact signed observations and forecasts,
the code, software checks and numerical environment. Use two one-thread
workers, one for each portion. Charge once for each full block and three
steps per block second to cover the three receiver pairs. Allow 180 seconds
with one additional attempt per unfinished task under the separately
qualified recovery workflow. Use no new source reads, flight fits or
reserved recordings. These are comparisons of relative GPS behavior
on one flight.
