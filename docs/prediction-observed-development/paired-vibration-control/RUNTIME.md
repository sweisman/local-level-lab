# Paired generated vibration evidence

The [predeclared plan](PLAN.md) uses 16 new seeds. Each task runs the same
generated sensor and receiver errors with physical vibration off and on,
then saves both earlier-only forecasts before scoring later positions.
The immutable source/environment manifest, charge journal, task receipts,
recovery qualification and saved forecasts and scores are retained.

All **16/16** pairs passed technical checks on one numerical thread, with
zero errors and no recovery task. The [saved-result audit](RESULT.md)
recomputes both scores from each task's forecast and later residuals.
Neither branch had a whole-history range failure. This is an exploratory
software control, not a replacement for the failed 256-history coverage
check or evidence from an aircraft. No aircraft original, reserved ESA
group or Earth-model fit was used.
