# Check the complete training-to-prediction adapter

Use the existing six known-answer model/processing fixtures. Replace only the
source remainder and its explicitly charged point-reference component. Keep
the observations, physical bounds, initial shared-error representation,
training certificates, coordinate scaling and known-truth checks unchanged.

For each fixture, fit no new parameters: construct the existing training
constraints, transfer the verified parent conditioning to the child domain,
compute bounds at two training times and one future time, and independently
audit the resulting rows and future endpoints. Future truth is inspected only
after the range is constructed. The target adapter may not request a fresh
native trajectory prediction.

## Separate finite allowance

- Six identities, all three physical models and both processing cases.
- 36 fixture native oracle calls and 468 packet visits.
- 36 old/new bounds and 2,574 logical steps: each fixture has three legacy
  bounds at two steps/packet and three direct bounds at nine steps/packet.
- Per target: one setup, one child proof, six parent supports, 12 training-row
  audits, one contraction, six future proposals, 24 supports and one truth
  audit. Three setups each for numerical source rows, domain and point
  derivatives; 39 steps each, 39 direct-formula steps and 39 body bounds.
- Preserve the frozen fixture's separate setup/proposal/support reservations.
- Four workers and one numerical thread each; four total threads. 30 seconds
  per target bound and 300 seconds overall, checked cooperatively.
- No retries, aircraft reads, optimizer starts, protected ESA data, signals or
  allowance expansion.

Freeze only after native and full-history qualification pass. All six answers,
audits and work reservations must pass before the new complete width comparison.
This is unblinded software qualification, not independent aircraft validation,
recording-scale adequacy or calibrated observational confidence.

[Full-history screen](../ilvis0-direct-range-preflight/INTERPRETATION.md) ·
[Roadmap](../ANALYSIS_ROADMAP.md).
