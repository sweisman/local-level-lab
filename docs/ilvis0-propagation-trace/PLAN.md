# Observe propagation accounting without changing arithmetic

The full projected-box comparison passes but reduces widths only 0.4–2.9%.
Observe six fixed generated cases, one per model/processing combination, using
orientation sector 4 throughout. These are diagnostic cases, not a replacement
for the complete orientation cover or original aircraft analysis.

Use Python's trace hook to inspect already-computed values in the unchanged
qualified enclosure. Do not replace numerical functions, recompute component
operations in a different order or alter physical bounds. The complete final
report and reference must match the sealed projected-bound report exactly.
The unit control checks exact report equality, both midpoint calculations per
packet, complete packet coverage and restoration of the trace hook.

Preserve per-packet force-reference and force-difference actions, increment and
residual-velocity allowances, and position departures. These conservative
quantities overlap and do not form an additive physical error budget. They
diagnose the calculation; they are not measured gyro or aircraft errors.

Freeze six identities, six bound replays and 9,600 reserved packet steps,
zero native integration calls and zero LP proposals. Four workers use one
thread each. Allow 600 cooperative seconds overall and 180 per observed bound
to accommodate tracing overhead. No retries, extensions, signals, original
aircraft reads, fits or protected ESA outcomes. Preserve any equality failure.

Only a fully matching trace may guide a subsequent mathematical candidate.
Tighter bounds require separate derivation and qualification; this observer
does not change scientific conclusions or release dependent aircraft fits.
