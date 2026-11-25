# Two more flights for checking recorded aircraft motion

Two paired-recorder controls completed with files already on hand. All eight
comparisons were scorable. Each fit used the earlier half to align the two
recorders, then measured disagreement in the later half. [Fixed plan](MOTION_FALLBACK_PLAN.md)

| Flight | Common support | Later rate disagreement at ¼ second | At one second | After averaging the one-second differences in ten-second blocks |
| --- | ---: | ---: | ---: | ---: |
| 20 Oct 2015 | 408 s | 17.83°/h RMS | 4.65°/h RMS | 1.42°/h RMS |
| 27 Oct 2015 | 427 s | 19.24°/h RMS | 5.35°/h RMS | 1.38°/h RMS |

The table uses the earlier-selected alignment and the elapsed packet clock.
The nominal clock gives the same rounded values. Six comparisons selected
zero shift. The other two selected one 5 ms packet in either direction.
Those shifts changed the later quarter-second and one-second disagreement
by less than 0.05°/h RMS. Averaging had a much larger effect. The result
measures the difference between recorders. An error shared by both could
still be present.

The 27 October flight is also a candidate for a separate camera check.
Four public reduced images were retrieved. The inspected preview shows
little stable detail, and the archive asks for an Earthdata sign-in to
retrieve the original full-resolution frame. The camera motion estimate
still needs usable original frames and qualified image processing. The
20 October DMS matches are orthorectified products, so their published
orientation cannot supply an independent camera check. [Archive coverage and method](MOTION_FALLBACK_PLAN.md)

Both tasks completed all 988 planned operations with zero Earth-model fits
and zero reserved ESA reads. Five software tests passed. The saved report
retains both clocks, earlier shift curves, and later scores. [Checked results](motion-fallback-result.json) ·
[Archive verification](motion-fallback-evidence/README.md)

```sh
env PYTHONPATH=analysis ~/venv/bin/python analysis/tests/run_numerical.py \
  --workers 1 --threads 1 -- ~/venv/bin/python -m lll.ilvis0_motion_fallback report
```
