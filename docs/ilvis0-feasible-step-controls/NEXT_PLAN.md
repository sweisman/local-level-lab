# Test the training gaps, not another optimizer

The completed trial qualifies its first-step component and preserves every
outcome. All six generated cases contain allowed calibrations whose later
north predictions differ by more than 20 m. There is no value in another
search intended to prove that this same problem has a narrower range.

The five earlier observations leave gaps as long as 150 seconds. The next
diagnostic will evaluate the **existing accepted north-extreme pair and original
calibration** for every model and processing case at one-second spacing, from
2 through 290 seconds. Keep the same input increments, physical bounds, original
five observations and later prediction at 438 seconds. No parameters are refitted.

This is a separately frozen software diagnostic: 18 fixed native batches,
at most four total numerical threads and ten minutes. All original epoch values
must reproduce exactly. Its detailed plan must be saved before launch.

At additional epochs there are no measured observations. Report whether the
three predicted position intervals could share an observation within ±1 m,
including the supplied numerical guard. Do not invent observed positions or
choose noise to make a candidate pass. Empty overlap would show that denser
training excludes this particular pair; nonempty overlap would leave its
ambiguity possible. Neither outcome qualifies an outer range or an aircraft
error law. Preserve all outcomes and keep V01 unqualified.

[Result](INTERPRETATION.md) · [Roadmap](../ANALYSIS_ROADMAP.md).
