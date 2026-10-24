# Corrected source packaging

The initial pilot ended after 72 charged setup failures and **zero native
calculations**. Its Python dependency walk omitted the C file used by the value
loader. No scientific fit or forecast ran. The completed run, input arrays,
charges and failure records remain unchanged.

The corrected definition explicitly includes both native translation units and
requires a smoke test that loads them from an isolated source snapshot. It
reuses the verified decoded input bytes from the failed run; it does not read
originals again or change the selection, splits, physical bounds, starts, weights,
scoring, solver or forecast equations.

Use a separate study identity and separately frozen allowance of 72 starts,
14,472 native calls and a 24-hour cooperative wall ceiling, with one worker and
four threads. The previous allowance is closed, not resumed or replenished.
Cumulative accounting therefore includes 72 failed setup identities plus up to
72 corrected identities. Preserve both runs in the public record. New failures
remain failures; this correction does not authorize retries or limit expansion.

[Original scientific plan](PLAN.md) · [Initial failure](../ilvis0-retrospective-prediction-pilot/README.md)
