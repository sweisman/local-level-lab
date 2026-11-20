# Single-pass ESA attempt found a covariance identity mistake

The separately frozen single-pass task rebuilt the full error operator within
its allowance, using 361,228 of 450,000 permitted native calls. It then
stopped at the training-prefix identity check. The check compared a hash of
the prefix's matrices with a hash of the original full training stream;
those hashes have different definitions and cannot be equal even when the
underlying early covariance is unchanged.

This is a **technical gate failure**, not a failed aircraft prediction. The
terminal task and charges are retained. No later GPS value was opened, no
conditional forecast was scored, and the scientific decision remains
**abstain**. The seven reserved ESA flight groups remain unopened.

The [corrected plan](CONDITIONAL_FORECAST_V3_PLAN.md) uses the same sealed
early inputs and verifies the replay with the early covariance's Gaussian
log-determinant and the whitened cost of the saved early residuals. Both are
quantities defined for the original and rebuilt operators. Only then will it
condition on earlier GPS errors and score the later section.
