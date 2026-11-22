# Combined forecast error scores improve, but the receiver checks disagree

Adding separate receiver covariances to a refitted shared forecast term
improves the summed omitted-window Gaussian score by **368.57 units**
under either inertial input convention. All eight donor fits choose a
shared covariance multiplier of **0.5**. Forecast paths and scored
positions stay fixed.

| GPS solution | Windows within the Student reference, original → combined | Gaussian score improvement |
| --- | ---: | ---: |
| `air1` | 7/8 → 2/8 | 26.88 |
| `mosaic03` | 3/8 → 5/8 | 208.84 |
| `pwrpak7` | 2/8 → 7/8 | 132.85 |

The table shows the point-rate convention. The increment convention
gives identical counts and nearly identical scores. Six `air1` scores
fall below the new reference. This indicates excess modeled uncertainty
for that receiver even though the overall predictive density improves.
Twelve of 24 receiver-window checks passed with the original covariance
and fourteen with the combined covariance. These counts reuse the same
eight windows and three GPS solutions sharing one antenna.

The combined model clears the planned score comparison. Accuracy and
coverage on other flights remain unqualified, and the seven reserved
flight groups stay closed. The next error model needs evidence about
which receiver differences represent errors in the original solution
and which arise from error correlations among all three solutions.

All eight tasks completed in 16.6 seconds. Five focused software checks
passed. The study used 392 charged calls and zero new trajectory fits.

[Frozen plan](ESA_ADDITIVE_RECEIVER_COVARIANCE_PLAN.md) ·
[Verified evidence](esa-additive-receiver-covariance-evidence/README.md)
