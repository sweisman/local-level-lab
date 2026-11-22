# Receiver-visible generated motion evidence

The [frozen pilot plan](PILOT_PLAN.md) fixes 16 fresh noise seeds and pairs
motion-off and motion-on histories at each seed. Each pair uses identical
generated gyro, accelerometer and receiver error draws. The added analytic
motion varies north position by about 0.2 m across the one-second receiver
reports. Both earlier-only forecasts are saved before the later positions
are scored.

All **16/16** pairs passed technical checks with no errors on one
numerical thread; no recovery task was needed. The
[saved-result audit](PILOT_RESULT.md) recomputes all scores. Neither arm
had a whole-history range miss, and the maximum paired change in the
largest standardized error was 0.0016. The 16 cases do not qualify
coverage or replace the failed 256-history gate. No aircraft original,
reserved ESA group or Earth-model fit was used.

The source/environment manifest, charge journal, task receipts, recovery
qualification and complete forecasts and scores are preserved here.
