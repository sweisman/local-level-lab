# Four repeat-turn opportunities on the opened ESA flight

The receiver-only screen found **four non-overlapping 400/120-second
forecast supports** in recording 187. The earlier development portion
and all three preselected short-block windows were excluded. The four
new supports contain three left turns and one right turn.

| Original receiver indices | First scoring index | Signed course change during the turn block |
| --- | ---: | ---: |
| 22,936–23,975 | 23,736 | −9.1° |
| 33,796–34,835 | 34,596 | −6.6° |
| 37,516–38,555 | 38,316 | −7.2° |
| 41,116–42,155 | 41,916 | +12.7° |

The screen used 37,604 receiver reports in two retained portions
and checked 626 complete 30-second blocks. Of 24 blocks with course
spans of at least 5°, four had quiet neighbors and a matched straight
control under the original rule. All four had enough data for the
longer forecast support. The short straight controls identify nearby
quiet motion, so a separate forecast plan still needs to establish
which full straight intervals to use as controls.

The generated test estimated the turn response and drift using the same
first 70 position errors in two cases. It reproduced the later positions
when the second turn had the same response and the drift stayed steady.
Reversing the second response and changing the drift after the cut left
the earlier coefficients unchanged and produced the expected east and
height errors. This verifies that the comparison can distinguish those
cases when the truth is known.

The four real supports are opportunities to test repeatability within
one flight. The inventory reads receiver timing and motion only. It
starts no model fit, uses no decoded IMU data and estimates no aircraft
error law. The next aircraft step is to qualify a fixed preparation and
forecast protocol for these supports, including how it handles a turn
in the opposite direction. Independent confirmation remains a separate
study.

[Plan and reproduction](ESA_REPEAT_TURN_PLAN.md) ·
[Frozen inputs](esa-repeat-turn-freeze.json) ·
[Full receiver inventory](esa-repeat-turn-result.json)
