# All 104 saved forecasts meet the fixed accuracy screen

Every saved forecast met the original position-error limits, including
the 67 whose fits failed their numerical stopping checks. Both starts
met the limits at all 40 cuts in the transfer study. All four starts met
them at all six cuts in the optimizer comparison. The studies overlap
in their recordings and test one specified-field globe model.

| Study | Passing accuracy screen, original numerical stop | Passing accuracy screen, no numerical stop | Smallest receiver-error margin | Median margin |
| --- | ---: | ---: | ---: | ---: |
| Twenty-group transfer | 30/30 | 50/50 | 0.31 m | 8.27 m |
| Optimizer comparison | 7/7 | 17/17 | 0.31 m | 8.38 m |

The screen uses 10 m horizontal RMS, 30 m height RMS, and 50 m and 150 m
maximum horizontal and height errors. In the transfer study, the
smallest margin across its 40 later-cut forecasts was **5.57 m**. The
smallest overall margin came from an earlier cut. In all 104 cases, the
horizontal RMS limit was the first one that a sufficiently large receiver
perturbation could reach.

The margin is the smallest per-epoch receiver error bound that would let an
adverse correction move a fixed forecast's score to a limit. It does not
estimate how large actual GPS errors were. These results separate forecast
accuracy on the recorded paths from numerical qualification. The original
study still has nine accepted later-cut groups, and the 67 failed stopping
checks keep their original labels. Independent aircraft accuracy and
prediction coverage remain open.

All 104 calculations were saved. Both completion envelopes were rejected
because the worker omitted the required scientific abstention field. The
report verifies the sealed score artifacts, original labels and saved
boundary values without repeating the study. The rejected envelopes and
their charges remain in the archive.

[Frozen plan](ACCURACY_MARGIN_PLAN.md) · [Per-forecast results](accuracy-margin.json) ·
[Verified evidence bundle](accuracy-margin-evidence/replay.zip)
