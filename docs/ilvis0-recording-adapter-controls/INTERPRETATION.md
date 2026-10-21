# Longer inputs reach the current calculation unchanged

**All six compatibility cases pass.** Three physical candidates and two
processing assumptions retain the complete four-minute generated inputs.
The old and current software interfaces give exactly matching positions,
all 27 calibration-derivative columns and warning flags at the checked points.
The 24 queries took 5.85 seconds.

Each query checks the first five seconds. Both interfaces call the same
numerical kernel, so this establishes compatible data handling, not an
independent physical validation or an accuracy guarantee over four minutes.
The original fixed-clock assumption remains. No short-example training
constraint or uncertainty certificate is transferred to the longer problem.

The next finite screen measures bound growth and runtime at the original
50-second endpoint. Useful complete-record ranges and an adequate observation
error model remain required before new aircraft prediction fits.

[Verified results](README.md) · [Frozen scope](PLAN.md) ·
[Growth screen](../ilvis0-recording-growth-screen/PLAN.md).
